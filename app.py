import streamlit as st
import pandas as pd
from graphviz import Digraph
from PIL import Image, ImageOps, ImageDraw
import os

# تنظیمات اصلی صفحه
st.set_page_config(page_title="شجره‌نامه هوشمند خاندان میری", layout="wide")

# ایجاد پوشه ذخیره‌سازی
if not os.path.exists("photos"):
    os.makedirs("photos")

DATA_FILE = "family_db.csv"

def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return pd.DataFrame(columns=["id", "name", "parent_id", "spouse_id", "gender", "birth_year", "bio", "photo"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def make_circle(img_path):
    """تبدیل عکس به دایره استاندارد"""
    try:
        img = Image.open(img_path).convert("RGBA")
        img = ImageOps.fit(img, (200, 200), centering=(0.5, 0.5))
        mask = Image.new('L', (200, 200), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, 200, 200), fill=255)
        img.putalpha(mask)
        circle_path = img_path.replace(".png", "_circle.png")
        img.save(circle_path)
        return circle_path
    except:
        return ""

# --- امنیت ---
PASSWORD = "miri" # رمز ورود را اینجا تغییر دهید
if "auth" not in st.session_state:
    st.session_state["auth"] = False

if not st.session_state["auth"]:
    st.title("🔐 ورود به پنل خاندان میری")
    pwd = st.text_input("رمز عبور خانوادگی:", type="password")
    if st.button("ورود"):
        if pwd == PASSWORD:
            st.session_state["auth"] = True
            st.rerun()
        else:
            st.error("رمز اشتباه است.")
    st.stop()

# --- برنامه اصلی ---
df = load_data()

st.sidebar.header("➕ ثبت عضو جدید")
with st.sidebar.form("add_member"):
    name = st.text_input("نام و نام خانوادگی")
    gender = st.selectbox("جنسیت", ["آقا", "خانم"])
    birth = st.number_input("سال تولد", 1200, 1405, 1370)
    
    # لیست اعضا برای انتخاب والدین و همسر
    members_list = ["هیچکدام"] + [f"{int(r['id'])}-{r['name']}" for _, r in df.iterrows()]
    parent = st.selectbox("فرزندِ کیست؟ (والد)", members_list)
    spouse = st.selectbox("همسرِ کیست؟", members_list)
    
    photo = st.file_uploader("آپلود عکس چهره", type=["jpg", "png", "jpeg"])
    bio = st.text_area("بیوگرافی کوتاه")
    
    submit = st.form_submit_button("ثبت در شجره‌نامه")

if submit and name:
    new_id = len(df) + 1
    p_id = parent.split("-")[0] if parent != "هیچکدام" else ""
    s_id = spouse.split("-")[0] if spouse != "هیچکدام" else ""
    
    path = ""
    if photo:
        temp = f"photos/{new_id}.png"
        with open(temp, "wb") as f:
            f.write(photo.getbuffer())
        path = make_circle(temp)
    
    new_row = pd.DataFrame([[new_id, name, p_id, s_id, gender, birth, bio, path]], columns=df.columns)
    df = pd.concat([df, new_row], ignore_index=True)
    save_data(df)
    st.sidebar.success("با موفقیت ثبت شد!")
    st.rerun()

# --- رسم نمودار ---
st.title("🌳 شجره‌نامه تعاملی میری")
if not df.empty:
    dot = Digraph(format='png')
    dot.attr(rankdir='TB', splines='ortho')

    for _, row in df.iterrows():
        color = "#FFD1DC" if row['gender'] == "خانم" else "#ADD8E6"
        p_path = os.path.abspath(row['photo']) if (pd.notna(row['photo']) and os.path.exists(row['photo'])) else ""
        
        # طراحی نود (Node)
        if p_path:
            label = f'''<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" BGCOLOR="{color}">
                        <TR><TD FIXEDSIZE="TRUE" WIDTH="60" HEIGHT="60"><IMG SRC="{p_path}"/></TD></TR>
                        <TR><TD><B>{row['name']}</B><BR/>{int(row['birth_year'])}</TD></TR>
                      </TABLE>>'''
        else:
            label = f'''<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" BGCOLOR="{color}">
                        <TR><TD><B>{row['name']}</B><BR/>{int(row['birth_year'])}</TD></TR>
                      </TABLE>>'''
        
        dot.node(str(int(row['id'])), label=label, shape="none")

    # ایجاد روابط
    for _, row in df.iterrows():
        if pd.notna(row['parent_id']) and str(row['parent_id']) != "":
            dot.edge(str(int(float(row['parent_id']))), str(int(row['id'])))
        
        if pd.notna(row['spouse_id']) and str(row['spouse_id']) != "":
            # ایجاد خط همسری افقی
            with dot.subgraph() as s:
                s.attr(rank='same')
                dot.edge(str(int(float(row['spouse_id']))), str(int(row['id'])), style="dashed", color="red", constraint="false")

    st.graphviz_chart(dot)
else:
    st.info("هنوز اطلاعاتی وارد نشده است. از منوی سمت راست اولین نفر را اضافه کنید.")