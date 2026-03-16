from groq import Groq

client = Groq(api_key=os.environ["GROQ_API_KEY"])

def btrieve_to_postgres(btrieve_code: str) -> str:
    """Конвертация Btrieve схемы в PostgreSQL DDL."""
    
    prompt = f"""
    Конвертируй Btrieve файловые определения в PostgreSQL DDL.
    
    ПРАВИЛА МАППИНГА:
    - Btrieve INTEGER(2) → SMALLINT
    - Btrieve INTEGER(4) → INTEGER  
    - Btrieve STRING(n)  → VARCHAR(n) или TEXT
    - Btrieve FLOAT      → DOUBLE PRECISION
    - Btrieve DATE       → DATE
    - Btrieve PRIMARY KEY → PRIMARY KEY + UNIQUE INDEX
    - Btrieve ALTERNATE KEY → UNIQUE INDEX или INDEX
    - BOpen/BRead → SELECT с курсором
    - BWrite      → INSERT ... ON CONFLICT DO UPDATE
    - BDelete     → DELETE
    - BGetNext    → курсор с FETCH NEXT
    
    ВХОДНОЙ КОД BTRIEVE:
    {btrieve_code}
    
    ВЫХОДИ ТОЛЬКО SQL DDL + Haskell postgresql-simple привязки.
    """
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=4096,
        temperature=0.1
    )
    return response.choices[0].message.content

# Пример использования
btrieve_sample = """
struct CustomerRecord {
    int    custId;        // Alternate Key
    char   custName[50];
    char   address[100];
    double balance;
    int    status;
};
// BOpen("CUSTOMER.BTR", ...)
// BRead(CUSTOMER, &rec, sizeof(rec), KEY_0)
"""
print(btrieve_to_postgres(btrieve_sample))
