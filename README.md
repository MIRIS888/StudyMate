# AI Studijní Asistent

Webová aplikace pro generování studijních materiálů pomocí umělé inteligence. Aplikace umožňuje analyzovat nahrané soubory nebo vybrané témata z databáze a vytvářet shrnutí, testové otázky a kartičky pro procvičování.

## Funkce

- 📁 **Nahrávání souborů**: Podporuje PDF, DOCX a TXT soubory
- 📚 **Předpřipravené materiály**: Databáze studijních materiálů podle předmětů a témat
- 🤖 **AI analýza**: Využívá OpenAI GPT pro generování studijních materiálů
- 📋 **Shrnutí látky**: Hlavní body a klíčové informace
- ❓ **Testové otázky**: Multiple-choice otázky s odpověďmi
- 🃏 **Kartičky**: Interaktivní kartičky s flip efektem pro procvičování

## Technologie

- **Backend**: Python Flask
- **Frontend**: HTML, CSS, JavaScript
- **AI**: OpenAI GPT-3.5-turbo
- **Zpracování souborů**: PyPDF2, python-docx
- **Databáze**: JSON soubor (pro ukázku)

## Instalace

### 1. Klonování repozitáře
```bash
git clone https://github.com/MIRIS888/StudyMate.git
cd StudyMate
```

### 2. Vytvoření virtuálního prostředí
```bash
python -m venv venv
# Windows
venv\\Scripts\\activate
# Linux/Mac
source venv/bin/activate
```

### 3. Instalace závislostí
```bash
pip install -r requirements.txt
```

### 4. Nastavení OpenAI API klíče
Vytvořte environment proměnnou nebo upravte soubor `app.py`:
```bash
# Windows
set OPENAI_API_KEY=your_openai_api_key_here

# Linux/Mac
export OPENAI_API_KEY=your_openai_api_key_here
```

Nebo upravte řádek v `app.py`:
```python
openai.api_key = "your_openai_api_key_here"
```

### 5. Spuštění aplikace
```bash
python app.py
```

Aplikace bude dostupná na: `http://localhost:5000`

## Struktura projektu

```
StudyMate/
├── app.py                 # Hlavní Flask aplikace
├── requirements.txt       # Python závislosti  
├── study_materials.json   # Databáze studijních materiálů
├── templates/
│   └── index.html        # Frontend aplikace
├── uploads/              # Dočasné nahrané soubory
└── README.md            # Dokumentace
```

## Použití

1. **Nahrání souboru**: Vyberte PDF, DOCX nebo TXT soubor z vašeho zařízení
2. **Výběr z databáze**: Zvolte předmět (Matematika, Čeština, Angličtina) a téma
3. **Analýza**: Klikněte na tlačítko "Analyzovat" a počkejte na zpracování
4. **Výsledky**: Prohlédněte si vygenerované shrnutí, otázky a kartičky

### Kartičky
- Kliknutím na kartičku se otočí a ukáže odpověď
- Ideální pro procvičování a memorování

### Testové otázky
- Multiple-choice formát s označenými správnými odpověďmi
- Zelené pozadí označuje správnou odpověď

## Rozšíření

### Přidání nových materiálů
Upravte soubor `study_materials.json`:
```json
{
  "NovýPředmět": {
    "NovéTéma": "Text materiálu pro analýzu..."
  }
}
```

### Změna AI modelu
V `app.py` upravte model v OpenAI volání:
```python
response = client.chat.completions.create(
    model="gpt-4",  # nebo jiný model
    messages=[{"role": "user", "content": prompt}],
    temperature=0.7
)
```

## Poznámky

- Pro funkčnost je potřeba platný OpenAI API klíč
- Aplikace je určena pro vzdělávací účely
- Maximální velikost nahrávaného souboru: 16MB
- Dočasné soubory se automaticky mažou po zpracování

## Požadavky

- Python 3.7+
- OpenAI API klíč
- Internetové připojení pro API volání