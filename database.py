# ملف مسئول عن فتح الاتصال بالداتا بيز


from sqlalchemy import create_engine
#Layer فوق psycopg2 يدير الاتصال

from sqlalchemy.orm import sessionmaker, DeclarativeBase
# DeclarativeBase : الـ Base class اللي كل Models هتورث منه عشان SQLAlchemy يعرف انه model or table


from dotenv import load_dotenv
#بتقرا ملف .env
import os
#os اللي بتخليكي تتعاملي مع الـ environment

load_dotenv()
#بتقرأ فايل الـ .env  وبتحط كل حاجة فيه في الـ environment.

DATABASE_URL = os.getenv("DATABASE_URL")
#بتجيبي قيمة DATABASE_URL من الـ environment.



engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine)
#بتعمل session مرتبطة بالـ engine — كل request هياخد session منها.
#مجرد مصنع بتصنع السيشن(قالب ليه ) لسه مفتحتهاش


class Base(DeclarativeBase):
    pass
# DeclarativeBase مجرد “نظام عام”
# لكن: Base = النسخة الخاصة بمشروعك
# DeclarativeBase = مجرد “نظام عام” لكن ... Base = النسخة الخاصة بمشروعك بحيث لو عايزة اضيف حاجه للموديل بتوعى مثلا

