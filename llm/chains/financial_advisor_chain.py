"""
FinSight AI Financial Advisor Chain.

Architecture:
  1. User query → embedding → Pinecone similarity search (RAG)
  2. Retrieved context (past transactions, insights) + system prompt
  3. GPT-4o with function calling for live data lookups
  4. Streamed response back to user

Requires: OPENAI_API_KEY, PINECONE_API_KEY in environment.
"""
import os
from typing import Optional, AsyncIterator
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser


SYSTEM_PROMPT = """You are FinSight AI, an expert personal financial advisor assistant with deep knowledge of:
- Personal budgeting and expense management
- Savings strategies and emergency fund planning
- Debt reduction methods (avalanche and snowball)
- Investment fundamentals (index funds, diversification)
- Tax-efficient financial planning basics

Your personality: warm, encouraging, clear, practical. You celebrate wins and gently guide improvements.

Rules:
- Always ground advice in the user's actual financial data when provided
- Never recommend specific stocks, crypto, or speculative investments
- For complex tax/legal matters, recommend a CPA or financial advisor
- Use concrete numbers and percentages in your advice
- Keep responses concise but actionable (3–5 sentences for simple questions, more for analysis)

User's Financial Context:
{context}
"""


class FinancialAdvisorChain:
    """
    LangChain-based financial advisor with RAG context injection.
    """

    def __init__(
        self,
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        use_rag: bool = True,
    ):
        self.model_name = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.use_rag = use_rag

        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            streaming=True,
        )

        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.vector_store = None

        if use_rag:
            self._init_vector_store()

    def _init_vector_store(self):
        """Initialize Pinecone vector store for RAG."""
        try:
            from langchain_pinecone import PineconeVectorStore
            import pinecone

            pc = pinecone.Pinecone(api_key=os.environ.get("PINECONE_API_KEY", ""))
            index_name = os.environ.get("PINECONE_INDEX_NAME", "finsight-transactions")

            if index_name in [idx.name for idx in pc.list_indexes()]:
                self.vector_store = PineconeVectorStore(
                    index_name=index_name,
                    embedding=self.embeddings,
                )
                print("✓ Pinecone vector store connected")
            else:
                print(f"⚠ Pinecone index '{index_name}' not found. RAG disabled.")
                self.use_rag = False
        except Exception as e:
            print(f"⚠ Pinecone unavailable: {e}. RAG disabled.")
            self.use_rag = False

    def _retrieve_context(self, query: str, user_id: str, k: int = 5) -> str:
        """Retrieve relevant transaction context for the query."""
        if not self.use_rag or not self.vector_store:
            return "No transaction history available."

        try:
            docs = self.vector_store.similarity_search(
                query,
                k=k,
                filter={"user_id": user_id},
            )
            if not docs:
                return "No relevant transaction history found."

            context_parts = []
            for doc in docs:
                context_parts.append(doc.page_content)
            return "\n".join(context_parts)
        except Exception as e:
            return f"Context retrieval unavailable: {e}"

    async def stream(
        self,
        messages: list,
        user_id: str,
        financial_summary: Optional[dict] = None,
    ) -> AsyncIterator[str]:
        """
        Stream the AI response token by token.

        Args:
            messages: List of {"role": "user"|"assistant", "content": "..."}
            user_id: For RAG context filtering
            financial_summary: User's current financial stats dict
        """
        # Build context from RAG + financial summary
        last_user_msg = next(
            (m["content"] for m in reversed(messages) if m["role"] == "user"), ""
        )
        rag_context = self._retrieve_context(last_user_msg, user_id)

        context_parts = []
        if financial_summary:
            context_parts.append(f"Current Financial Summary:\n{_format_summary(financial_summary)}")
        if rag_context and rag_context != "No transaction history available.":
            context_parts.append(f"Relevant Transaction History:\n{rag_context}")

        context = "\n\n".join(context_parts) if context_parts else "No financial context available."

        # Build message list for LLM
        lc_messages = [SystemMessage(content=SYSTEM_PROMPT.format(context=context))]
        for msg in messages:
            if msg["role"] == "user":
                lc_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                lc_messages.append(AIMessage(content=msg["content"]))

        # Stream response
        async for chunk in self.llm.astream(lc_messages):
            if chunk.content:
                yield chunk.content

    def invoke(self, query: str, user_id: str, financial_summary: Optional[dict] = None) -> str:
        """Synchronous single-turn invocation."""
        context = ""
        if financial_summary:
            context = _format_summary(financial_summary)

        messages = [
            SystemMessage(content=SYSTEM_PROMPT.format(context=context or "No context available")),
            HumanMessage(content=query),
        ]
        response = self.llm.invoke(messages)
        return response.content


def _format_summary(summary: dict) -> str:
    """Format financial summary dict into readable context string."""
    parts = []
    if "monthly_income" in summary:
        parts.append(f"Monthly income: ${summary['monthly_income']:,.2f}")
    if "monthly_expenses" in summary:
        parts.append(f"Monthly expenses: ${summary['monthly_expenses']:,.2f}")
    if "savings_rate" in summary:
        parts.append(f"Savings rate: {summary['savings_rate']:.1f}%")
    if "health_score" in summary:
        parts.append(f"Financial health score: {summary['health_score']}/100")
    if "top_categories" in summary:
        parts.append(f"Top spending categories: {', '.join(summary['top_categories'])}")
    if "budget_status" in summary:
        parts.append(f"Budget status: {summary['budget_status']}")
    return "\n".join(parts)
