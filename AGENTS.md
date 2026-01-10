# AGENTS.md - Sibom Scraper Assistant

Repository configuration and workflows for autonomous agents.

## 🎯 Arquitectura de Agentes

**Este proyecto usa `.agents/` como fuente principal de coordinación para agentes AI.**

- **Leer primero:** `.agents/specs/` - Arquitectura concisa del proyecto
- **Respetar siempre:** `.agents/steering/` - Reglas obligatorias para agentes
- **Consultar si necesario:** `.kiro/specs/` - Análisis técnico profundo

Ver [`.agents/COORDINACION.md`](.agents/COORDINACION.md) para detalles completos.

## 🏗️ Project Structure

This is a polyglot repository with two main applications:

- `/chatbot`: Next.js 15 (TypeScript) frontend for querying bulletins.
- `/python-cli`: Python 3.13 CLI tool for scraping SIBOM.

## 🚀 Common Commands

### Chatbot (Next.js)

- **Install**: `cd chatbot && npm install`
- **Dev**: `cd chatbot && npm run dev`
- **Build**: `cd chatbot && npm run build`
- **Lint**: `cd chatbot && npm run lint`
- **Test**: `cd chatbot && npm test`
- **Test Coverage**: `cd chatbot && npm run test:coverage`

### Scraper (Python CLI)

- **Setup**: `cd python-cli && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt`
- **Run Scraper**: `python3 sibom_scraper.py --limit 5`
- **Run Tests**: `pytest` (requires venv activation)
- **Extraction Tools**: Scripts like `monto_extractor.py` and `table_extractor.py` are used for post-processing.

## 🛠️ Development Workflow

1. **Environment**: Both apps require a `.env` file (see `.env.example` in respective directories).
2. **Data Flow**: The scraper saves JSON files to `python-cli/boletines/`. The chatbot's RAG system consumes these files.
3. **Commit Convention**: Follow existing style (mostly Spanish/English mix, concise).
4. **Agent Rules**: Always check `.agents/` directory for detailed architecture specs before making structural changes.

## 🧪 Testing Policy

- **Chatbot**: Use `vitest`. Ensure new logic in `src/lib` has corresponding tests in `__tests__`.
- **Python**: Use `pytest`. Tests are located in `python-cli/tests/`.

## 📚 Documentation for Agents

### Quick Start for AI Agents

1. **Read:** [`.agents/specs/`](.agents/specs/) - Understand project architecture
2. **Follow:** [`.agents/steering/`](.agents/steering/) - Respect mandatory patterns
3. **Reference:** [`.kiro/specs/`](.kiro/specs/) - Consult for technical details (optional)

### Configuration Files

- **Claude Code:** See `.claude/CLAUDE.md`
- **Droid/Factory:** See `.factory/config.yml`
- **Coordination:** See `.agents/COORDINACION.md`

---

**For complete documentation, see:** [`.agents/README.md`](.agents/README.md)
