def crystal_to_pdfslave(rpt_xml: str) -> str:
    """Конвертация CrystalReports в pdf-slave YAML шаблон."""
    
    # Используем Gemini для понимания сложной структуры RPT
    model = genai.GenerativeModel("gemini-2.0-flash-exp")
    
    prompt = f"""
    Конвертируй CrystalReports XML/RPT определение в pdf-slave YAML шаблон.
    
    МАППИНГ:
    - ReportHeader → header секция
    - PageHeader   → page-header
    - Detail       → body с repeat-блоком  
    - GroupHeader  → group-header
    - GroupFooter  → group-footer
    - ReportFooter → footer
    - Subreport    → вложенный template
    - Formula Field → Haskell выражение в {{{{ }}}}
    - Parameter Field → переменная шаблона
    - DatabaseField → поле из JSON/контекста
    - CrystalReports формулы → Haskell функции
    
    ТАКЖЕ создай:
    1. Haskell тип для контекста данных отчёта (Aeson FromJSON)
    2. Функцию рендеринга через pdf-slave библиотеку
    
    CrystalReports XML:
    {rpt_xml}
    """
    
    response = model.generate_content(prompt)
    return response.text

def crystal_to_jrxml(rpt_xml: str) -> str:
    """Альтернатива: конвертация в JasperReports JRXML."""
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    
    prompt = f"""
    Конвертируй CrystalReports в JasperReports JRXML формат.
    
    МАППИНГ ЭЛЕМЕНТОВ:
    - TextObject    → <staticText> или <textField>
    - FieldObject   → <field> + <textField>
    - FormulaField  → <variable> с выражением
    - GroupSection  → <group>
    - Subreport     → <subreport>
    - GraphObject   → <barChart>/<pieChart> etc.
    
    CrystalReports XML:
    {rpt_xml}
    
    Верни валидный JRXML для JasperReports 6.x
    """
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=8192
    )
    return response.choices[0].message.content
