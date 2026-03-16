def cpp_qt_to_qml(cpp_widget_code: str) -> str:
    """Конвертация C++ Qt виджетов в QML."""
    
    # Mistral Codestral специализирован на коде
    import mistralai
    client = mistralai.Mistral(api_key=os.environ["MISTRAL_API_KEY"])
    
    prompt = f"""
    Конвертируй C++ Qt виджет код в современный QML.
    
    МАППИНГ:
    - QMainWindow      → ApplicationWindow
    - QDialog          → Dialog
    - QPushButton      → Button (QtQuick.Controls)
    - QLineEdit        → TextField
    - QTableView       → TableView + TableModel
    - QTreeView        → TreeView
    - QComboBox        → ComboBox
    - QLabel           → Text / Label
    - QVBoxLayout      → ColumnLayout
    - QHBoxLayout      → RowLayout
    - QGridLayout      → GridLayout
    - connect(signal)  → Connections / onSignal
    - QThread          → WorkerScript / Qt.callLater
    - Haskell backend  → QML ↔ Haskell через HsQML или QtQuick.XmlListModel
    
    C++ Qt КОД:
    {cpp_widget_code}
    
    Дай: 1) QML файл 2) Haskell HsQML привязки если нужны
    """
    
    response = client.chat.completions.create(
        model="codestral-latest",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=8192
    )
    return response.choices[0].message.content
