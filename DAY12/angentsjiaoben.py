import os

from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain.tools.retriever import create_retriever_tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
# from langchain_core.tools import create_retriever_tool, tool
from langchain_openai import ChatOpenAI

from  ragjiaoben import retriever, chain

cli = ChatOpenAI(
    api_key="sk-5e387f862dd94499955b83ffe78c722c",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model="qwen-max",
)

ge01 = create_retriever_tool(
    retriever=retriever,
    name="ge01",
    description="根据用户输入的股票名称，返回一个具体的股票信息"
)


@tool
def ge02(mo):
    """
    根据用户输入的投入金额，计算年均收入
    :param mo:
    :return:
    """
    pro = ChatPromptTemplate.from_template(
        """
        你是一个股票收益计算器，根据用户输入的投入金额:{mo}，计算年均收入。
        例如:
        投资 10万港币(约 307股):
        乐观情景(年均+20%):约12万港币
        中性情景(年均+8%):约10.8万港币
        悲观情景(年均-15%):约8.5万港币
        """
    )
    ds = pro | cli
    print(ds.invoke({"mo": mo}))
    return ds.invoke({"mo": mo})


@tool
def ge03(name):
    """
    根据用户输入的股票名称，从知识库检索信息并分析该股票
    :param name:
    :return:
    """
    # 使用RAG系统查询股票信息
    question = f"请提供关于{name}股票的详细信息和分析"
    stock_info = chain.invoke(question)

    # 基于检索到的信息进行进一步分析
    analysis_prompt = ChatPromptTemplate.from_template(
        """
        基于以下股票信息，提供专业的风险分析和投资建议：

        股票信息：{stock_info}

        请从以下角度分析：
        1. 价格趋势分析（一个月和一年变化）
        2. 行业前景分析
        3. 风险评估
        4. 投资建议（请注明投资有风险）

        股票名称：{name}
        """
    )

    analysis_chain = analysis_prompt | cli
    result = analysis_chain.invoke({"stock_info": stock_info, "name": name})
    print(result)
    return result


tools = [ge01, ge02, ge03]

pro = ChatPromptTemplate.from_messages(
    [
        ('system', '''你是一个专业的股票投资顾问，拥有以下工具：
        1. ge01: 检索股票的基本信息（价格、变化率、行业等）
        2. ge02: 根据投入金额计算不同情景下的年均收益
        3. ge03: 基于知识库数据进行深度股票分析和风险评估

        请按以下步骤为用户提供服务：
        1. 首先使用ge01获取股票基本信息
        2. 然后使用ge03进行专业的股票分析和风险评估
        3. 最后使用ge02计算投资收益预测
        4. 综合所有信息给出投资建议

        请确保提醒用户投资有风险，建议仅供参考。'''),
        ('user', '股票名称:{name},投入金额:{mo}'),
        MessagesPlaceholder(variable_name="agent_scratchpad")
    ]
)

ce = create_openai_tools_agent(cli, tools, pro)

fd = AgentExecutor(
    agent=ce,
    tools=tools,
    verbose=True
)
print(fd.invoke({"name": "苹果", "mo": 10000})["output"])