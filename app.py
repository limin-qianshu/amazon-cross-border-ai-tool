import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from openai import OpenAI
import os
import json

# 智谱API初始化
client = OpenAI(
    api_key=os.getenv("ZHIPU_API_KEY"),
    base_url="https://open.bigmodel.cn/api/paas/v4/"
)

# 页面配置
st.set_page_config(page_title="跨境电商外贸分析助手", layout="wide")
st.title("🌐 跨境电商亚马逊评论分析 & 文案合规助手")
tab1, tab2, tab3, tab4 = st.tabs(["📊 评论痛点分析", "📧 询盘邮件生成", "✨ Listing润色", "⚠️ 合规极限词检测"])

# ========== Tab1：评论分析 + 图表 ==========
with tab1:
    st.subheader("上传买家评论CSV文件，自动提炼痛点并生成分析图")
    uploaded_file = st.file_uploader("上传csv文件", type="csv")
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.dataframe(df.head(8))
        st.info(f"一共读取 {len(df)} 条评论")
        all_text = "\n".join(df.iloc[:,0].astype(str).tolist())
        prompt = """
你是跨境电商运营分析师，根据下面亚马逊买家评论，提炼用户负面痛点，只统计负面痛点。
【硬性输出规则】
只返回标准JSON，不要```json、不要任何解释文字、中文、换行、注释。
输出必须完整闭合，不允许中途截断。
格式严格示例: {"Shipping Slow":2,"Bad Material":1}
评论内容:
""" + all_text
        resp = client.chat.completions.create(
            model="glm-4-flash",
            temperature=0,
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
            start_idx = res_text.find("{")
            end_idx = res_text.rfind("}")
            if start_idx >= 0 and end_idx > start_idx:
                json_str = res_text[start_idx : end_idx + 1]
                data = json.loads(json_str)
                # 绘图
                labels = list(data.keys())
                values = list(data.values())
                fig, ax = plt.subplots()
                ax.bar(labels, values)
                ax.set_title("Negative Feedback Count")
                ax.set_ylabel("Count")
                plt.xticks(rotation=30)
                st.pyplot(fig)
            else:
                raise Exception("找不到合法JSON")
        except Exception as e:
            st.warning("解析JSON失败，无法自动生成图表，请检查大模型返回格式")

# ========== Tab2：询盘邮件生成 ==========
with tab2:
    st.subheader("输入客户需求，生成英文外贸询盘回复邮件")
    requirement = st.text_input("买家需求描述：")
    if st.button("生成询盘邮件") and requirement:
        res = client.chat.completions.create(
            model="glm-4-flash",
            temperature=0.3,
            messages=[{"role":"user","content":f"你是外贸业务员，写一封地道专业的英文回复询盘邮件。需求：{requirement}"}]
        )
        st.text_area("生成邮件", res.choices[0].message.content, height=300)

# ========== Tab3：Listing润色 ==========
with tab3:
    st.subheader("输入原始Listing文案，优化适合亚马逊英文商品标题描述")
    listing_text = st.text_area("原始Listing文案：")
    if st.button("润色Listing") and listing_text:
        res = client.chat.completions.create(
            model="glm-4-flash",
            temperature=0.3,
            messages=[{"role":"user","content":f"优化这段亚马逊Listing英文文案，适合跨境平台，地道自然：{listing_text}"}]
        )
        st.text_area("润色结果", res.choices[0].message.content, height=300)

# ========== Tab4：极限词合规检测 ==========
with tab4:
    st.subheader("检测文案里亚马逊违规极限词、合规风险")
    check_text = st.text_area("待检测文案：")
    if st.button("开始合规检测") and check_text:
        res = client.chat.completions.create(
            model="glm-4-flash",
            temperature=0,
            messages=[{"role":"user","content":f"检查下面英文亚马逊商品文案里面是否有违规极限词、合规风险，标出风险点并给出修改建议：{check_text}"}]
        )
        st.text_area("检测结果", res.choices[0].message.content, height=300)
