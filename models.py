from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Float, Integer, ForeignKey, Table, Column
from database import Base
# الـ Base اللي عملناها في database.py — دي الأم اللي هيورث منها الجدول.



student_course = Table(
    "student_course",
    Base.metadata,
    Column("student_id", Integer, ForeignKey("students.id")),
    Column("course_id", Integer, ForeignKey("courses.id"))
)
#جدول الربط فى علاقه many to many 
#لو مش محتاجه غير الربط بعملها كده 
#لكن محتاجه ازود تاريخ تسجيل وبتاع اعملها كلاس بحيث اعرف اتعامل مع البيانات بالobject 

class Student(Base):
#Base بيعمل الجدول الفعلي في الـ Database    
    __tablename__ = "students"
#بتعرفي الجدول الـ __tablename__ بيقول لـ SQLAlchemy اسم الجدول في الداتا بيز.

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    #Mapped[int] ← نوع الـ column في Python
    #primary_key=True ← ده الـ ID الفريد لكل row
    #index=True ← بيسرع البحث بالـ id
    name: Mapped[str] = mapped_column(String(100))
    #str:نوع البيانات في Python
    #string(100):نوع العمود في SQL/database
    #كل واحدة ليها types  مختلفة بتفهمها
    age: Mapped[int] = mapped_column(Integer)
    grade: Mapped[float] = mapped_column(Float)
    Email: Mapped[str | None] = mapped_column(String(255),nullable=True)
    #str | None يعكس أن القيمة فعلًا ممكن تكون NULL.
    teacher_id: Mapped[int] = mapped_column(Integer, ForeignKey("teachers.id", ondelete="SET NULL"),
    nullable=True)
    #ده الوحيد اللى بيبقى عمود فعلا فى الجدول وده اللى بيربط الجدولين
    #ondelete="SET NULL" في الـ ForeignKey:بيقول للـ Database "لو الـ Teacher اتمسح حط NULL في الـ teacher_id بتاع الـ Students. ده بيحصل على مستوى الـ Database نفسها.
    #nullable=True في الـ teacher_id:لازم تضيفيهاعشان لو الـ teacher_id هيبقى NULL، الـ Database لازم تسمح بيه من غيرها هيديكي error.

    teacher: Mapped["Teacher"] = relationship("Teacher", back_populates="students")
    # ده مش عمود في الداتا بيز.دي SQLAlchemy بتعملها عشان تسهّل التعامل في Python.
    #بيها تقدرى تعملى student.teacher على طول لكن الداتا بيز متعرفش غير students.teacher_id
    #من غيرها لازم تعملى كويرى كامله teacher = db.query(Teacher).filter(Teacher.id == student.teacher_id).first()
                                       #print(teacher.name)
    courses: Mapped[list["Course"]] = relationship(
    "Course",
    secondary=student_course,
    back_populates="students"
    )
    profile: Mapped["Profile"] = relationship("Profile", back_populates="student", uselist=False)
    #uselist=False: بيقول لـ SQLAlchemy مش محتاجة ترجعيلى list — رجعيلي object واحد بس.
    #يعنى مش زى teacher.student بترجع  [student1, student2, ...]


#now we are going to make relationships:)
class Teacher(Base):
    __tablename__ = "teachers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    students: Mapped[list["Student"]] = relationship("Student", back_populates="teacher",passive_deletes=True)    

    #Mapped[list["Student"]]: دي Type Hint بتقول ان المتغير students هيحتوي List من كائنات Student.
    #relationship("Student"): فيه علاقة بين Teacher و Student.
    #back_populates="teacher": العلاقة دي مرتبطة بـ attribute اسمه teacher موجود في Model Student.فالعلاقة بقت في الاتجاهين
    #في الـ relationship:بيقول لـ SQLAlchemy "متتدخلش — خلي الـ Database هي اللي تتحكم في الـ delete." يعني بيعتمد على الـ ondelete اللي حطيناه في الـ ForeignKey


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    students: Mapped[list["Student"]] = relationship(
        "Student", 
        secondary=student_course, 
        # ده بيقول لـ SQLAlchemy "الجدول الوسيط بيني وبين الجدول التاني هو student_course." وهو بيتحكم في العلاقة تلقائياً من غير ما تكتبي أي SQL. ✅
        back_populates="courses"
    )



class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    bio: Mapped[str] = mapped_column(String(500), nullable=True)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id"), unique=True)
    #unique=True في الـ student_id:بيقول للـ Database "مش ممكن يبقى عندك Profile لأكتر من Student يعني لو حاولتي تضيفي Profile تاني لنفس الـ Student هيرفض و ده اللي بيعمل الـ One to One فعلاً.
    student: Mapped["Student"] = relationship("Student", back_populates="profile")    


#هنبتدى jwt
#1- دلوقتي هنعمل جدول Users يخزن اى تسجيل جديد
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    #unique=True : بيمنع تسجيل أكتر من user بنفس الـ username. 
    hashed_password: Mapped[str] = mapped_column(String(255))