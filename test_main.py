#قبل اى حاجه بننزل pytest : المكتبة اللي بتشغل الـ tests وتقولك أيهم نجح وأيهم فشل.


from fastapi.testclient import TestClient
#بتجيبي أداة بتحاكي requests على الـ API من غير ما تشغلي uvicorn فعلياً.
from main import app
#بتجيبي الـ FastAPI app بتاعتك.

client = TestClient(app)
#بتعملي "client وهمي" يقدر يبعت requests للـ app بتاعتك.

#أي function اسمها بادئ بـ test_ — pytest بيعرف إنها test ويشغلها تلقائياً.
def test_get_students():
    response = client.get("/students")
    #بتبعتي GET request فعلي على /students — تماماً زي ما تعمليه في Swagger، بس من غير Browser.
    assert response.status_code == 200
    # بتتأكدي إن الشرط ده صح. لو الـ status code مش 200 — الـ test بيفشل ويوريكي رسالة error
    #response ← ده الـ object اللي رجع بعد ما بعتي الـ request.
    #response.status_code ← الرقم اللي السيرفر رجعه (200, 404, 500...).
    #assert X == Y ← لو X بيساوي Y فعلاً الكود يكمل عادي وبدون أي ناتج.  X مش بيساوي Y — Python بترمي AssertionError ويعتبر pytest الـ test "فشل."

#بتتأكدى ان لو حد طلب student مش موجود ال api هترجع 404 فعلا(error handling)
def test_get_nonexistent_student():
    response = client.get("/students/99999/courses")
    assert response.status_code == 404

#بتتأكدي إن الـ JWT protection شغالة — إنك مش تقدري تضيفي Student من غير Token. ده اختبار أمان مهم جداً.
def test_add_student_without_token():
    response = client.post("/students", json={
        "name": "Test Student",
        "age": 20,
        "grade": 85.0,
        "teacher_id": 1
    })
    assert response.status_code == 401



#بتتأكدي إن الـ response مش بس status code 200 — لكن كمان إنها list فعلاً، مش dict أو حاجة غلط.
def test_get_students_returns_list():
    response = client.get("/students")
    assert isinstance(response.json(), list) 
    #isinstance() دي دالة جاهزة في Pythonبتسأل هل المتغير ده من النوع ده؟ isinstance(object, type)




