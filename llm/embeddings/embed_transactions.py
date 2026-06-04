"""
Transaction embedding pipeline.
Converts transactions into vector embeddings and upserts to Pinecone.
Run periodically (e.g., nightly) to keep vector store fresh.

Usage:
    python -m llm.embeddings.embed_transactions --user-id <uuid>
"""
import os
import sys
import argparse
import time
from typing import List, Optional
from pathlib import Path


def build_transaction_text(tx: dict) -> str:
    """Convert a transaction dict into a searchable text representation."""
    parts = []
    if tx.get("merchant_name"):
        parts.append(f"Merchant: {tx['merchant_name']}")
    if tx.get("description"):
        parts.append(f"Description: {tx['description']}")
    if tx.get("amount"):
        parts.append(f"Amount: ${abs(float(tx['amount'])):.2f}")
    if tx.get("category"):
        parts.append(f"Category: {tx['category']}")
    if tx.get("transaction_date"):
        parts.append(f"Date: {tx['transaction_date']}")
    if tx.get("is_recurring"):
        parts.append("Recurring: Yes")
    return " | ".join(parts)


def embed_and_upsert(
    transactions: List[dict],
    user_id: str,
    batch_size: int = 100,
) -> dict:
    """
    Embed transaction list and upsert to Pinecone.

    Args:
        transactions: List of transaction dicts
        user_id: User identifier for metadata filtering
        batch_size: Number of vectors per upsert batch

    Returns:
        Summary dict with upserted count
    """
    try:
        import pinecone
        from openai import OpenAI
    except ImportError:
        return {"error": "pinecone or openai package not installed", "upserted": 0}

    api_key = os.environ.get("OPENAI_API_KEY")
    pinecone_key = os.environ.get("PINECONE_API_KEY")
    index_name = os.environ.get("PINECONE_INDEX_NAME", "finsight-transactions")

    if not api_key or not pinecone_key:
        return {"error": "Missing OPENAI_API_KEY or PINECONE_API_KEY", "upserted": 0}

    oai = OpenAI(api_key=api_key)
    pc = pinecone.Pinecone(api_key=pinecone_key)

    # Get or create index
    existing = [idx.name for idx in pc.list_indexes()]
    if index_name not in existing:
        pc.create_index(
            name=index_name,
            dimension=1536,  # text-embedding-3-small dimension
            metric="cosine",
            spec=pinecone.ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        print(f"Created Pinecone index: {index_name}")
        time.sleep(5)

    index = pc.Index(index_name)
    total_upserted = 0

    for i in range(0, len(transactions), batch_size):
        batch = transactions[i:i + batch_size]
        texts = [build_transaction_text(tx) for tx in batch]

        # Get embeddings from OpenAI
        response = oai.embeddings.create(
            model="text-embedding-3-small",
            input=texts,
        )
        embeddings = [item.embedding for item in response.data]

        # Prepare Pinecone vectors
        vectors = []
        for j, (tx, embedding) in enumerate(zip(batch, embeddings)):
            vector_id = f"{user_id}_{tx.get('transaction_id', f'tx_{i+j}')}"
            vectors.append({
                "id": vector_id,
                "values": embedding,
                "metadata": {
                    "user_id": user_id,
                    "transaction_id": str(tx.get("transaction_id", "")),
                    "merchant_name": tx.get("merchant_name", ""),
                    "category": tx.get("category", ""),
                    "amount": float(tx.get("amount", 0)),
                    "transaction_date": str(tx.get("transaction_date", "")),
                    "text": texts[j][:1000],  # Pinecone metadata limit
                },
            })

        index.upsert(vectors=vectors)
        total_upserted += len(vectors)
        print(f"  Upserted batch {i // batch_size + 1}: {len(vectors)} vectors")

    return {
        "user_id": user_id,
        "total_upserted": total_upserted,
        "index_name": index_name,
    }


def delete_user_embeddings(user_id: str) -> dict:
    """Delete all embeddings for a user (GDPR compliance)."""
    try:
        import pinecone
        pc = pinecone.Pinecone(api_key=os.environ.get("PINECONE_API_KEY", ""))
        index = pc.Index(os.environ.get("PINECONE_INDEX_NAME", "finsight-transactions"))
        index.delete(filter={"user_id": user_id})
        return {"message": f"Deleted all embeddings for user {user_id}"}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Embed transactions into Pinecone")
    parser.add_argument("--user-id", type=str, required=True)
    parser.add_argument("--data-path", type=str, default="ml/data/processed/transactions.csv")
    args = parser.parse_args()

    import pandas as pd
    df = pd.read_csv(args.data_path)
    user_txs = df[df["user_id"] == args.user_id].to_dict(orient="records")

    if not user_txs:
        # Use first user in dataset for demo
        first_user = df["user_id"].iloc[0]
        user_txs = df[df["user_id"] == first_user].head(100).to_dict(orient="records")
        args.user_id = first_user
        print(f"User not found. Using first user: {first_user}")

    print(f"Embedding {len(user_txs)} transactions for user {args.user_id}...")
    result = embed_and_upsert(user_txs, args.user_id)
    print(f"Result: {result}")
