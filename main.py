from fastapi import FastAPI, Depends, HTTPException, Request
#Depends ← جديدة عليكي — بتحقن الـ database session في كل function تلقائياً.
#HTTPException ← بترجعي error احترافي للـ client بدل return("failed").
from fastapi.responses import JSONResponse

from pydantic import BaseModel, ConfigDict

from sqlalchemy.orm import Session
from database import SessionLocal, engine

from models import Student, Base, Teacher , Course

#بيفتح ملف الموديلز وتضيفهم تلقائيًا للـ metadata.

from sqlalchemy.orm import joinedload
#عشان ال Eager Loading
from google import genai
#عشان الai integratin

from passlib.context import CryptContext
#passlib: عشان تشفري الباسورد (Hashing) وتتحققي منه بعد كده.
#خلى بالك نصبي bcrypt version أقدم متوافقة مع passlib عشان يفهموا بعض وبايثون يفهمهم
import bcrypt

from fastapi.security import OAuth2PasswordRequestForm


from models import User

from jose import jwt
#بتجيبي الأداة اللي بتعمل وتتحقق من JWT Tokens.
from datetime import datetime, timedelta
##بتستخدميهم عشان تحددي إمتى الـ Token هينتهي.
import os

from fastapi.security import OAuth2PasswordBearer
#ده Class جاهز من FastAPI فيه منطق (logic) خاص بقراءة Bearer Token من الـ Request.

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
#ده بيعمل object هنستخدمه عشان:
#نشفر الـ password وقت Register , نقارن الـ password وقت Login
#schemes=["bcrypt"] ← بيقول "استخدمي bcrypt في التشفير."

SECRET_KEY = os.getenv("SECRET_KEY")
#بتجيبي الـ Secret Key من .env — ده اللي بيوقع الـ Token وبيتأكد إنه مش مزور.
ALGORITHM = "HS256"
#ده نوع التشفير المستخدم في توقيع الـ Token — HS256 هو الأكتر استخداماً.
ACCESS_TOKEN_EXPIRE_MINUTES = 30
#بعد كام دقيقة الـ Token هينتهي — هنا 30 دقيقة.



class UserCreate(BaseModel):
    username: str
    password: str


app = FastAPI()

#خلاص بقينا نستخدم alembic (Alembic لا يعرف أن create_all هو الذي أنشأ الجداول هو يعتمد على جدول:alembic_version)
#Base.metadata.create_all(bind=engine)
#base: ده الـ Base class اللي كل Models بتورث منه.
#metadata: يعني كأنه registry أو سجل.
#create_all(): روح شوف كل الجداول المعرفة في الـ models واعملها في الداتا بيز لو مش موجودة.
#السطر كله اعمل كل الجداول الموجودة في الـ models داخل الداتا بيز باستخدام الاتصال الحالي.


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
#1- يحط السيشن فى argument fبحيث وقت ما يستدعى الفانكشن دى يفتح سيشن
#2-yield :  كأنها بالظبط return بس مبتقفلش الفانكشن زيها يعنى بتقوله خده ونفذ اللى اللى هتنفذه وارجعلييييي تانى كمل الفانكشن 
# 3- try: عشان حتى لو حصل ايرور يرجع برضو
# 4- وفى الاخر بيرجع عشان يقفل السيشن






#تخيلي إن Student عنده password — هتبعتيه في الـ response للـ client؟ 😱
# الـ client بيبعت
class StudentCreate(BaseModel):
    name: str
    age: int
    grade: float
    teacher_id: int
    course_ids: list[int] = []

# إنتي بترجعي
class StudentResponse(BaseModel):
    id: int       
    name: str
    age: int
    grade: float
    teacher_id: int
    model_config = ConfigDict(from_attributes=True)
    #Pydantic بالعادي بيتوقع dict — لو بعتيله SQLAlchemy object هيديكي error. فهنا بنقوله ان دى attributes and objects.
#خدى بالك ان فى الرد الموضوع مختلف هو مش بياخد من الكلاينت جسون هو بياخد من الكود وpydantic غبي شويه :)

#للتعديل:  كل الـ fields اختيارية — يعني بتبعتي بس اللي عايزة تعدليه
class StudentUpdate(BaseModel):
    name: str | None = None     # اختياري
    age: int | None = None      # اختياري
    grade: float | None = None  # اختياري
    teacher_id: int | None = None

#str | None ← يعني الـ field ممكن تبقى String أو None
#= None ← يعني لو الـ client مبعتش الـ field دي — هتبقى None تلقائياً.




class StudentSchema(BaseModel):
    name: str
    age: int
    grade: float
#studentschema for validation
# FastAPI يفحص البيانات من اليوزر أول ما توصل وترجع ايرور لو غلط قبل ما يلمس الداتا بيز أصلا.
#student in models for creationg couloms 
#بتبنى الجدول وتعرف النوع عشان تتأكد قبل تخزينها حاولى تفرقى بين الكود والداتا بيز نفسها لأن أحيانًا يبقى عندك جدول مبنى قبل كده  فيه 20 عمود لكن الـ API بتاع إنشاء المستخدم محتاج 3 أعمدة فقط. فلو اعتمدتي على الـ Model لوحده هتربطي الـ API بشكل الجدول مباشرة، وده بيصعب التطوير بعد كده.
    teacher_id: int
    course_ids: list[int] = []


class teacherSchema(BaseModel):
    name: str


class courseSchema(BaseModel):
    name: str    

##for ai integratin
class QuestionSchema(BaseModel):
    question: str
  


#2. Register endpoint — تسجيل مستخدم جديد مع تشفير الـ password
@app.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    hashed_password = pwd_context.hash(user.password)
    new_user = User(username=user.username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created successfully"}

#3- دلوقتي هنعمل الـ function اللي بتولد الـ Token. ضيفي:
def create_access_token(data: dict):
 #إحنا بنستقبل Dictionary. بيبقى فيها معلومات ال user
    to_encode = data.copy()
    #إحنا بنستقبل Dictionary عشان منعدلش على الـ data الأصلية.  
    #لو عملنا:to_encode = data هيبقوا الاثنين بيشاوروا على نفس الـ Dictionary.
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    #بزود تاريخ الانتهاء على البينات الموجوده فى الdictionary تحت مفتاح exp .  خدى بالك انه dic عشان كده اتزود بالطريقه دى
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
   #  jwt.encode:بتديله المعلومات ال3 وبتولدي الـ Token الفعلي 
    return encoded_jwt


class LoginSchema(BaseModel):
    username: str
    password: str


@app.post("/login")
#def login(credentials: LoginSchema, db: Session = Depends(get_db)):
#لما التوكن يطلع وعايزين نستخدمه فى /student هنستخدم postman
#عشان swagger لما تضغطي Authorize بيبعت الـ credentials كـ form-data مش JSON بس الـ Login endpoint بتاعتك بيتوقع JSON — فبيديك error.
def login(credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
#حل تانى نغير الدات اللى هيستقبلها للform-data
#OAuth2PasswordRequestForm ده class جاهز من FastAPI — بدل ما الـ client يبعت JSON، بيبعت form-data.
#Depends() هنا من غير argument — يعني FastAPI نفسه هيعمل الـ injection من الـ form-data اللي جاية في الـ request.
    user = db.query(User).filter(User.username == credentials.username).first()
    
    if not user or not pwd_context.verify(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    #not user ← لو الـ username مش موجود خالص
    #not pwd_context.verify(...) ← لو الـ password غلط
    access_token = create_access_token(data={"sub": user.username})
    #data={"sub": user.username} ← بنحط الـ username جوه الـ Token (dictionary) تحت مفتاح sub — ده standard في JWT معناه "Subject" يعني "مين ده الـ Token بتاعه."
    return {"access_token": access_token, "token_type": "bearer"}
#بترجعي الـ Token للـ Client بشكل منظم:
#access_token ← الـ Token نفسه
#token_type: "bearer" ← ده standard بحيث Authorization: Bearer <token>" دى الصيغه اللى بيتحفظ بيها فى ال header  
#هنا الفرونت بيستلم ويحفظه locally ويكتب برضو اللى يخليه يتحط فى الباكيت مع الريكويست


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
#ده Class جاهز من FastAPI فيه منطق (logic) خاص بقراءة Bearer Token من الـ Request.
#tokenUrl="login" مجرد معلومة وصفيه بتقول "الـ Endpoint المسؤولة عن الحصول على Token اسمها login لكن مش بيروح فعلا , ده بيخلي Swagger UI يعرض زرار "Authorize" تلقائياً.
#انما بيجيبها من الهيدر عادى عن طريق class logic اللى بيخليه يبص فى الهيدر يشوف Authorization: Bearer eyJ123 ويستخرج eyJ123
 

#4. Dependency بتتحقق من الـ Token في كل request
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    #دي Dependency — هتتحقن في أي endpoint عايزة تحميه. بتاخد الـ Token من الـ Header تلقائياً.
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        #jwt.decode:ده أول مرحلة تحقق المكتبة نفسها بتتأكد من التوقيع (Signature)و exp لو حاجه منهم غلط تروح للexcept
        #لو كله تمام ترجع ال payload من التوكين
        username = payload.get("sub")
        #ـ بتجيبي الـ username اللي جوه sub.
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        #لو الـ Token مش فيه username يرجع 401
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    #كان لازم try فى دى عشان jwt.decode() ممكن تعمل crash من جوة المكتبة، فمحتاجة تمسكي الـ Exception دي بـ try/except وتحوليها لـ HTTPException مفهومة للـ client.

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user
#الخطوه الجايه بحقن current_user: User = Depends(get_current_user) فى اي end point عايزة احميه 
#قبل ما تشغل الـ Endpoint، نفذ الدالة get_current_user وخد الـ Return بتاعها وحطه في current_user. ولو فيها ايرور الداله هتقف والemdpoint مش هيتنفذ
#بتضمن إن عندك المستخدم الحالي جاهز للاستخدام، ومتحقق من هويته بالفعل. user: type hint للكلاس بتاع التسجيل
#فى الendpoints اللى هنا مستخدمش اليوزر اللى بيرجع لكن قدام ممكن احتاجه زى هو ادمن ولا لا

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    #print(request.url)
    #print(exc) هيعرفونى الايرور والطلب كان ايه
    return JSONResponse(
        status_code=500,
        content={"detail": "حصل خطأ غير متوقع، حاولي تاني بعدين"}
    )
#@app.exception_handler(Exception): بتقولي لـ FastAPI "لو حصل أي Exception روح الـ function دي."
#request ← الـ request اللي كان بيتنفذ لما حصل الـ error.exc ← الـ Exception نفسها اللي حصلت. Exception: ده الايرور الاب بيشير لاغلب الايرورز
#JSONResponse: بتخليه يرجعه جيسون عشان global_exception_handler مش endpoint عادي — ده handler خارج الـ FastAPI routing system.فمش بيتحكم فيه زى العادى

#for ai integratin
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
#بعمل client كانه وسيط بين تطبيقى موديل الذكاء بتجيب ال key وبتقول للمكتبة لو فى المستقبل احتجتى تكلمى Gemini، استخدمى الـ API Key ده
#اللى جاى بيطبع احدث الموديلات لجيمناى المتاحه ليا استخدمها لانهم كل شوية يحدثوهم فممكن بعد حبه ده ميشتغلش
#for model in client.models.list():
   # print(model.name)
    
@app.post("/ai/ask")
def ask_about_students(
    body: QuestionSchema,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)    #بيحمى الـ endpoint.
):
    students = db.query(Student).all()
    
    students_data = "\n".join([
        f"ID: {s.id}, Name: {s.name}, Age: {s.age}, Grade: {s.grade}"
        for s in students
    ])
    #بتجيبي كل الطلاب من الـ Database وبتحوليهم لـ نص عادي — عشان Gemini مش بيفهم Python objects، بيفهم نص بس.
    #f-string للتحويل , "\n".join: دى بتاخد List من الـ Strings وتجمعهم فى String واحدة والفاصل بينهم هو "\n"سطر جديد
    
    prompt = f"""
    You are a school assistant. Here is the students data:
    {students_data}
    
    Answer this question based on the data above:
    {body.question}
    """
   # ده الـ Prompt — يعني التعليمات اللي بتبعتيها لـ Gemini. 
    
    response = client.models.generate_content(model="gemma-4-31b-it", contents=prompt)
    #هنا لأول مرة حصل اتصال بالإنترنت.
    #يا وسيط Client استخدم الـ model ده، وابعت له الـ contents دي.
    return {"answer": response.text}
# .text:بياخد التيكست بس من جوه الرد لان فيه كمان كذا حاجه تانى

#بترجع كل الـ students — يعني list.
@app.get("/students", response_model=list[StudentResponse])
def get_students(db: Session = Depends(get_db)):
    students = db.query(Student).all()
    return students
#:session ده مجرد نوع المتغير->Type Hint
#depends: Dependency Injection بيحقن الداله بالداتا بيز من الفانكشن 
#query(Student):اعمل Query على جدول Student. كانها SELECT * FROM students


@app.get("/teacher")
def get_teachers(db: Session = Depends(get_db)):
    teachers = db.query(Teacher).all()
    return teachers



@app.get("/course")
def get_course(db: Session = Depends(get_db)):
    course = db.query(Course).all()
    return course

#response_model: بتخلى الreturn لو هيرجع يبقى بالresponseschema  (بمعنى انه بيفلتر من اللى داخل لو فى حاجه مينفعش ترجع فى الرد زى باسوورد)
#  و موجوده فى ال url لانها بتتعمل قبل ما ترجع للكلاينت على طول يعنى فى layer fastapi,pydantic
@app.post("/students", response_model=StudentResponse)
def add_student(student:StudentCreate, db: Session = Depends(get_db),  current_user: User = Depends(get_current_user)):
    new_student = Student(name=student.name, age=student.age, grade=student.grade, teacher_id=student.teacher_id)

    #many to mamy relation
    for course_id in student.course_ids:
        course = db.query(Course).filter(Course.id == course_id).first()
        if course:
            new_student.courses.append(course)
    #teacher_id:هو عمود حقيقي واحد في جدول students مستنى منك رقم.
    #لكن الكورسات هى كذا كورس جوه كورس واحد يعنى مستني منك  Courses Objects --> course1, course2,... مش [1,2] لكن انتى بتاخديهم وترجعيهاله اوبجكت من جدول الكورسات وهو لوحده بقا يروح الجدول التاى ويخزنها بطريقت ويربطه بالطالب بتاعه 

    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    return new_student
#db.add ← بيحضر الـ student للإضافة
#db.commit ← بيحفظه في الـ Database فعلاً
#db.refresh ← بيجيب البيانات المحدثة من الـ Database، زي الـ id الجديد
    

@app.post("/teacher")
def add_teacher(teacher: teacherSchema, db: Session = Depends(get_db)):
    new_teacher = Teacher(name=teacher.name)
    db.add(new_teacher)
    db.commit()
    db.refresh(new_teacher)
    return new_teacher

@app.post("/course")
def add_course(course: courseSchema, db: Session = Depends(get_db)):
    new_course = Course(name=course.name)
    db.add(new_course)
    db.commit()
    db.refresh(new_course)
    return new_course


@app.put("/students/{id}",response_model=StudentResponse)
def update_student(id: int, updated: StudentUpdate, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    #عامله زىreturn الفرق إن raise بترجع error response للـ client، وreturn بترجع response عادية. 
   # student.name = updated.name
    #student.age = updated.age
    #student.grade = updated.grade

#تبع ال studentupdate *الحاجه اللى فيها نون متبعتهاش *هتتسجل نون فى الداتا بيز
    if updated.name is not None:
        student.name = updated.name
    if updated.age is not None:
        student.age = updated.age
    if updated.grade is not None:
        student.grade = updated.grade

    if updated.teacher_id is not None:
        teacher = db.query(Teacher).filter(Teacher.id == updated.teacher_id).first()
        if not teacher:
            raise HTTPException(status_code=404, detail="Teacher not found")
        student.teacher_id = updated.teacher_id
    db.commit()
    db.refresh(student)
    return student
#.first() → رجع أول نتيجة فقط
#raise HTTPException: وقف تنفيذ الدالة وارجع Response فيه خطأ 404 مع توضيح لليوزر.

@app.delete("/students/{id}")
def delete_student(id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    db.delete(student)
    db.commit()
    return {"message": "deleted"}




#قاعده فى اى nasted..
class StudentInTeacher(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)

class TeacherResponse(BaseModel):
    id: int
    name: str
    students: list[StudentInTeacher] = []
    model_config = ConfigDict(from_attributes=True)

#نطبق شوية  Querying (Lazy vs Eager, Filter, Join)

#1 — جيبي كل Teachers مع Students بتوعهم:
@app.get("/teachers/with-students", response_model=list[TeacherResponse])
#لما بترجعي Teacher object جواه students (nasted opject) فpydantic بيتروش 
#فعملنا سكيما لكل واحد بمعلوماته اللى محتاجينها ترجع..
def get_teacher_students(db: Session = Depends(get_db)):
    teachers = db.query(Teacher).options(joinedload(Teacher.students)).all()
    #Eager Loading:بنستخدم joinedload عشان SQLAlchemy من البداية تجيب:المدرسين والطلاب مع بعض.
    return teachers

#filter
#2 — جيبي كل Students بتاع Teacher *معين*:
@app.get("/teachers/{teacher_id}/students")
def get_teacher_students2(teacher_id: int, db: Session = Depends(get_db)):
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
       raise HTTPException(status_code=404, detail="Teacher not found")
    return teacher.students
#:)ممكن اعملها كده على طول students = db.query(Student).filter(Student.teacher_id == teacherID).all()
#ال id فى ال url احسن -->  look in "restapi" كأنه بيحاول يمثل الداتا بيز في شكل URLs Teacher
                                                                                           #└── Students   فطبيعى يبقى /teachers/1/students هات طلبة المدرس ده 
#3 — جيبي كل Courses بتاع Student *معين*:
@app.get("/students/{student_id}/courses")
def get_student_course(student_id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
       raise HTTPException(status_code=404, detail="Student not found")
    return student.courses

#4 — سجلي Student في Course بعد ما اتعمل
@app.post("/students/{student_id}/courses/{course_id}")
def enroll_student_in_course(student_id: int, course_id: int , db: Session = Depends(get_db)):
     student = db.query(Student).filter(Student.id == student_id).first() 
     if not student:
        raise HTTPException( status_code=404, detail="Student not found")

     course = db.query(Course).filter(Course.id == course_id).first()
     if not course:
        raise HTTPException( status_code=404, detail="Course not found")
     
     if course not in student.courses:
#لمنع مشكلة اضافة نفس العلاقه مرتين
      student.courses.append(course)
     db.commit()
     db.refresh(student)
     return student