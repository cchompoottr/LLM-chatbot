import ollama
import psycopg2
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("sentence-transformers/all-MiniLM-L12-v2")

# connect PostgreSQL
def get_connection():
    return psycopg2.connect(
        dbname="mydb",
        user="admin",
        password="1234",
        host="localhost",
        port="5432"
    )

# สร้าง documents ในฐานข้อมูล
def create_documents_table():
    conn = get_connection()
    cur = conn.cursor()
    
    # vector similarity search)
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    
    # ลบตารางเดิมหากมีอยู่
    cur.execute("DROP TABLE IF EXISTS documents;")
    
    cur.execute("""
        CREATE TABLE documents (
            id SERIAL PRIMARY KEY,
            content TEXT,
            embedding vector(384)
        );
    """)
    
    conn.commit()
    cur.close()
    conn.close()

# insert doc + embedding 
def insert_document(content, embedding):
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("INSERT INTO documents (content, embedding) VALUES (%s, %s)", (content, embedding))
    
    conn.commit()
    cur.close()
    conn.close()

# semantic search
def query_postgresql(query_text, k=5):
    # แปลง query เป็น embedding
    query_embedding = model.encode(query_text).tolist()
    
    # แปลง embedding เป็น string สำหรับ SQL
    query_embedding_str = "[" + ", ".join(map(str, query_embedding)) + "]"
    
    conn = get_connection()
    cur = conn.cursor()
    
    # ดึงข้อมูลที่มี embedding ใกล้เคียงกับ query จากคล้ายที่สุด
    cur.execute("""
        SELECT content, embedding <=> %s::vector AS similarity_score
        FROM documents
        ORDER BY similarity_score ASC
        LIMIT %s;
    """, (query_embedding_str, k))
    
    results = cur.fetchall()
    cur.close()
    conn.close()
    
    return results

# ใช้ LLM ตอบคำถาม
def generate_response(query_text):
    # ค้นหาเอกสารที่เกี่ยวข้อง
    retrieved_docs = query_postgresql(query_text, 5)

    # รวมข้อความที่ได้มาเป็น context สำหรับ prompt
    context = "\n".join([doc[0] for doc in retrieved_docs])
    
    # สร้าง prompt (context + คำถามจากผู้ใช้)
    prompt = f"Answer the question based on the following context:\n{context}\n\nQuestion: {query_text}"
    
    response = ollama.chat(model="llama3.2", messages=[
        {"role": "system", "content": "You are a docter."},  
        {"role": "user", "content": prompt}
    ])

    return response["message"]["content"]
