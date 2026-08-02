FROM python:3.11-slim
#بتقولي "ابدئي بـ Image جاهز فيه Python 3.11و slim لأنها نسخة أخف. 
#دلوقتى فى ايمدج عباره عن linux ,python

WORKDIR /app
#بتعملي فولدر اسمه /app جوه الـ Container وتدخلي فيه — زي cd /app.

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
#pip install -r requirements.txt:فيقرأ الملف وينزل كل المكتبات الموجودة فيه.
#-no-cache-dir:علشان بعد ما ينزل الـ Packages، يمسح الملفات المؤقتة (Cache)، فيخلي حجم الـ Image أصغر.
COPY . .
#بتنقلي باقي ملفات المشروع كلها جوه /app.

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
#بتقولي "لما الـ Container يشتغل، نفذي الأمر ده" — يعني شغلي السيرفر.
#--host 0.0.0.0 ← اقبلي connections من أي مكان لو سيبتيها 127.0.0.1 مش هتقدري توصلي للـ API من برا الـ Container.
#مش هيتنفذ أثناء الـ Build هيتحفظ فقط داخل الـ Image
