# Quickstart - .agents/

**Tiempo de lectura:** 2 minutos

---

## 🎯 Lo Esencial

```
.agents/ define → .opencode/ ejecuta → .kiro/ referencia
```

- **`.agents/`** = Tu capa de dominio (QUÉ hacer)
- **`.opencode/`** = Runtime de OpenCode (CÓMO ejecutar)
- **`.kiro/`** = Referencia técnica (detalles profundos)

---

## 📁 Estructura

```
.agents/
├── README.md              # 👈 LEE ESTO PRIMERO (manual completo)
├── agents/                # Definiciones de agentes (YAML)
├── prompts/               # Prompts reutilizables
├── steering/              # Reglas de código (obligatorias)
├── specs/                 # Pointer a .kiro/
└── hooks/                 # Scripts de sincronización
```

---

## 🚀 Comandos Rápidos

```bash
# Leer manual completo
cat .agents/README.md

# Crear nuevo agente
vim .agents/agents/mi-agente.yaml
git add .agents/agents/mi-agente.yaml
git commit -m "agents: agregar mi-agente"

# Sincronizar con OpenCode (backup)
python .agents/hooks/sync_to_opencode.py

# Ver estado
python .agents/hooks/sync_status.py
```

---

## 📖 Guías

| Quiero... | Leo esto |
|-----------|----------|
| Entender todo | `.agents/README.md` |
| Crear un agente | `.agents/agents/README.md` |
| Ver cambios | `.agents/CHANGELOG.md` |
| Reglas de código | `.agents/steering/*.md` |
| Detalles técnicos | `.kiro/specs/` |

---

## ✅ Reglas de Oro

1. **`.agents/` define, `.opencode/` ejecuta** - NUNCA al revés
2. **Portabilidad** - `.agents/` funciona con cualquier herramienta
3. **Commit frecuente** - `.agents/` evoluciona con el proyecto
4. **Sincronización automática** - OpenCode lee `.agents/` directamente

---

## 🆘 ¿Olvidaste algo?

```bash
# Leer manual completo
cat .agents/README.md

# Ver estado de sincronización
python .agents/hooks/sync_status.py
```

---

**Siguiente paso:** Lee `.agents/README.md` para el manual completo 🚀
