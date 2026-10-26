import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from zhipuai import ZhipuAI
from dotenv import load_dotenv
import os
import json

# 加载密钥
load_dotenv()
client = ZhipuAI(api_key=os.getenv("ZHIPU_API_KEY"))

# ---------------- 页面配置 ----------------
st.set_page_config(page_title="跨境电商外贸分析助手", layout="wide")
st.title("🌐 跨境电商亚马逊评论分析 & 文案合规助手")
tab1, tab2, tab3, tab4 = st.tabs(["📊 评论痛点分析", "📧 询盘邮件生成", "✍ Listing润色", "⚠️ 合规极限词检测"])

# -------- Tab1：评论分析 + 图表 --------
with tab1:
    st.subheader("上传买家评论CSV文件，自动提炼痛点并生成分析图")
    uploaded_file = st.file_uploader("上传csv文件", type="csv")
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.dataframe(df.head(8))
        st.info(f"一共读取 {len(df)} 条评论")
        all_text = "\n".join(df.iloc[:,0].astype(str).tolist())
        prompt = f"""
你是跨境电商运营分析师，根据下面亚马逊买家评论，提炼用户反馈痛点，只统计负面痛点。
输出硬性要求：
仅返回标准JSON，不要```json、```、任何解释文字、中文、换行说明。
格式示例：{{"Shipping Slow":2,"Bad Material":1}}
评论内容：
{all_text}
        """
        resp = client.chat.completions.create(
            model="glm-4-flash",
            messages=[{"role":"user","content":prompt}]
        )
        st.markdown("### 分析结果")
        res_text = resp.choices[0].message.content
        res_text = res_text.strip()
        res_text = res_text.removeprefix("```json").removesuffix("```")
        res_text = res_text.strip()
        st.text_area("原始返回", res_text, height=200)
        # 尝试解析json绘图
        try:
            data_json = json.loads(res_text)
            names = list(data_json.keys())
            counts = list(data_json.values())
            fig, ax = plt.subplots()
            ax.bar(names, counts)
            plt.xticks(rotation=45, ha="right")
            plt.tight_layout()
            st.pyplot(fig)
        except Exception as e:
            st.warning("解析JSON失败，无法自动生成图表，请检查大模型返回格式")

# -------- Tab2：询盘邮件 --------
with tab2:
    st.subheader("生成外贸询盘英文邮件")
    content = st.text_area("输入产品信息、需求")
    if st.button("生成询盘邮件") and content.strip():
        p = f"""
你是跨境亚马逊卖家助理。用户发来的是海外买家的询盘，请你以卖家的身份，写一封地道简洁的英文回复邮件，带上邮件主题，专业友好，不要markdown加粗符号。
买家询盘内容：
{content}
        """
        r = client.chat.completions.create(model="glm-4-flash", messages=[{"role":"user","content":p}], temperature=0.5)
        st.markdown("### 生成邮件")
        st.text_area("邮件文本", r.choices[0].message.content, height=300)

# -------- Tab3：Listing润色 --------
with tab3:
    st.subheader("亚马逊Listing文案润色")
    txt = st.text_area("粘贴原始Listing文案")
    if st.button("润色") and txt.strip():
        p = f"""
优化下面亚马逊商品Listing英文文案，地道、适合海外买家阅读，适合亚马逊平台，不要夸大违规词汇：
{txt}
        """
        r = client.chat.completions.create(model="glm-4-flash", messages=[{"role":"user","content":p}], temperature=0.5)
        st.markdown("### 优化后文案")
        st.text_area("结果", r.choices[0].message.content, height=300)

# -------- Tab4：合规词检测 --------
with tab4:
    st.subheader("检测文案里面亚马逊违规极限词")
    check_text = st.text_area("粘贴需要检查的商品文案")
    if st.button("开始合规检测") and check_text.strip():
        p = f"""
检查下面文案里面的违规极限词、夸大宣传词，列出风险词并给出修改建议：
{check_text}
        """
        r = client.chat.completions.create(model="glm-4-flash", messages=[{"role":"user","content":p}], temperature=0.3)
        st.markdown("### 检测结果")
        st.text_area("结果", r.choices[0].message.content, height=300)