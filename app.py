import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from openai import OpenAI
import os
import json
from dotenv import load_dotenv
load_dotenv()

# 智谱API初始化
client = OpenAI(
    api_key=os.getenv("ZHIPU_API_KEY"),
    base_url="https://open.bigmodel.cn/api/paas/v4/"
)

# 页面配置
st.set_page_config(page_title="跨境电商外贸分析助手", layout="wide")
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    /* 外层页面U型圆角边框 */
    .stApp {
        background-color: #eef1f5;
    }
    .block-container {
        border: 1px solid #a7b0bd;
        border-radius: 24px;
        padding: 24px;
        background: #ffffff;
        max-width: 95%;
        margin: 20px auto;
    }
    .card{
        border: 1px solid #c6d8f0;
        background-color: #ffffff;
        padding: 20px;
        border-radius: 16px;
        margin: 12px 0px;
        box-shadow: 0 2px 8px rgba(198, 216, 240, 0.3);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 12px;
        border: 1px solid #c6d8f0;
        padding: 6px 14px;
        background-color: #f4f8fd;
    }
    .stTabs [aria-selected="true"] {
        background-color: #c6d8f0 !important;
        color: #2c4260 !important;
    }
    /* 美化按钮、输入框、文本域 */
    .stButton>button {
        border-radius: 10px;
        border: 1px solid #c6d8f0;
        background: #f4f8fd;
        color: #2c4260;
    }
    .stButton>button:hover {
        background: #c6d8f0;
    }
    .stTextInput>div>div>input,
    .stTextArea>div>div>textarea {
        border-radius: 10px;
        border: 1px solid #c6d8f0;
    }
</style>
""", unsafe_allow_html=True)

st.title("🌐 跨境电商AIGC外贸智能助手")
tab1, tab2, tab3, tab4 = st.tabs(["📊 评论痛点分析", "📧 询盘邮件生成", "✨ Listing润色", "⚠️ 合规极限词检测"])

# ========== Tab1：评论分析 + 图表 + 运营优化建议 ==========
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

        # 尝试解析json绘图 + 生成运营建议
        try:
            start_idx = res_text.find("{")
            end_idx = res_text.rfind("}")
            if start_idx >= 0 and end_idx > start_idx:
                json_str = res_text[start_idx : end_idx + 1]
                data = json.loads(json_str)
                # ========== 替换后的绘图代码 ==========
                labels = list(data.keys())
                values = list(data.values())
                fig, ax = plt.subplots(figsize=(10, 5))
                ax.bar(labels, values, color="#c6d8f0")
                ax.set_title("Negative Feedback Count", color="#2c4260")
                ax.set_ylabel("Count", color="#2c4260")
                # 调整标签：倾斜+右对齐，防止挤在一起
                plt.xticks(rotation=30, ha='right')
                # 自动适配布局，把文字完整放进画布
                plt.tight_layout()
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                st.pyplot(fig)

                # 根据痛点数据生成运营优化建议
                st.markdown("### 💡 基于痛点的产品&运营优化建议")
                with st.spinner("正在根据痛点图表生成优化方案..."):
                    advice_prompt = f"""
你是亚马逊跨境电商资深运营，下面是商品买家负面痛点统计：
{json.dumps(data, ensure_ascii=False, indent=2)}
请根据这份痛点数据，给出清晰、落地的改进建议，分产品改进、物流优化、Listing文案调整三个板块，用简洁专业的中文输出，适合卖家直接参考。
"""
                    advice_resp = client.chat.completions.create(
                        model="glm-4-flash",
                        temperature=0.4,
                        messages=[{"role":"user","content":advice_prompt}]
                    )
                    st.write(advice_resp.choices[0].message.content)
            else:
                raise Exception("找不到合法JSON")
        except Exception as e:
            st.warning("解析JSON失败，无法自动生成图表，请检查大模型返回格式")
            st.error(f"错误详情：{str(e)}")

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
