# Guía de Contribución

¡Gracias por tu interés en contribuir a SIBOM IA! 🎉

Este es un proyecto de desarrollo individual, pero acepto contribuciones de la comunidad siguiendo estas guías.

---

## 📋 Tabla de Contenidos

- [Código de Conducta](#código-de-conducta)
- [¿Cómo puedo contribuir?](#cómo-puedo-contribuir)
- [Proceso de Desarrollo](#proceso-de-desarrollo)
- [Guías de Estilo](#guías-de-estilo)
- [Sistema de Versionado](#sistema-de-versionado)
- [Reportar Bugs](#reportar-bugs)
- [Sugerir Funcionalidades](#sugerir-funcionalidades)

---

## 🤝 Código de Conducta

Este proyecto sigue un código de conducta simple:

- **Sé respetuoso**: Trata a todos con respeto y profesionalismo
- **Sé constructivo**: Criticas constructivas, no destructivas
- **Sé paciente**: Este es un proyecto mantenido por una persona
- **Sé claro**: Comunicación clara y concisa

---

## 🎯 ¿Cómo puedo contribuir?

### 1. Reportar Bugs

Usa el template de [Bug Report](.github/ISSUE_TEMPLATE/bug_report.md) para:
- Describir el problema claramente
- Incluir pasos para reproducir
- Proporcionar screenshots si aplica
- Especificar tu entorno (navegador, OS, versión)

### 2. Sugerir Funcionalidades

Usa el template de [Feature Request](.github/ISSUE_TEMPLATE/feature_request.md) para:
- Explicar el problema que resuelve
- Describir tu solución propuesta
- Considerar alternativas
- Estimar el impacto

### 3. Mejorar Documentación

Usa el template de [Documentation](.github/ISSUE_TEMPLATE/documentation.md) para:
- Reportar docs faltantes o incorrectas
- Sugerir mejoras de claridad
- Corregir typos o errores

### 4. Contribuir Código

Ver [Proceso de Desarrollo](#proceso-de-desarrollo) abajo.

---

## 🔧 Proceso de Desarrollo

### Setup Inicial

```bash
# 1. Fork el repositorio en GitHub

# 2. Clonar tu fork
git clone https://github.com/TU-USUARIO/sibom-scraper-assistant.git
cd sibom-scraper-assistant

# 3. Agregar upstream
git remote add upstream https://github.com/mrtn/sibom-scraper-assistant.git

# 4. Instalar dependencias
cd chatbot && bun install
cd ../python-cli && pip install -r requirements.txt

# 5. Copiar .env.example a .env y configurar
cp .env.example .env
nano .env
```

### Workflow de Desarrollo

```bash
# 1. Crear una branch desde main
git checkout main
git pull upstream main
git checkout -b feature/nombre-descriptivo

# 2. Hacer cambios y commits siguiendo Conventional Commits
git add .
git commit -m "feat: agregar búsqueda por rango de fechas"

# 3. Pushear a tu fork
git push origin feature/nombre-descriptivo

# 4. Crear Pull Request en GitHub
# Usa el template de PR y completa toda la información
```

### Antes de Enviar un PR

**Checklist obligatorio:**

- [ ] Tests pasan localmente (`bun run test`)
- [ ] Build funciona (`bun run build`)
- [ ] Linter pasa (`bun run lint`)
- [ ] Código sigue las convenciones del proyecto
- [ ] Documentación actualizada (si aplica)
- [ ] Commits siguen Conventional Commits
- [ ] PR usa el template completo

---

## 📝 Guías de Estilo

### TypeScript / React

**Convenciones:**
- Componentes en PascalCase: `MyComponent.tsx`
- Hooks en camelCase: `useMyHook.ts`
- Types/Interfaces: exportar desde `types.ts`
- No usar `any` (usar `unknown` si necesario)
- Usar arrow functions: `const MyComponent = () => {}`
- Props destructuring: `({ prop1, prop2 }: Props)`

**Ejemplo:**

```typescript
// ✅ Bien
interface UserProps {
  name: string;
  age: number;
}

export const UserCard = ({ name, age }: UserProps) => {
  return (
    <div className="card">
      <h2>{name}</h2>
      <p>{age} años</p>
    </div>
  );
};

// ❌ Mal
export function UserCard(props: any) {
  return (
    <div className="card">
      <h2>{props.name}</h2>
    </div>
  );
}
```

### Python

**Convenciones:**
- Seguir PEP 8
- Type hints en funciones públicas
- Docstrings en formato Google
- Imports ordenados con `isort`
- Formateado con `black`

**Ejemplo:**

```python
# ✅ Bien
def extract_normativa(
    html_content: str,
    municipality: str
) -> NormativaEntry:
    """Extrae normativa de HTML.
    
    Args:
        html_content: Contenido HTML del boletín
        municipality: Nombre del municipio
        
    Returns:
        Entrada de normativa extraída
        
    Raises:
        ValueError: Si el HTML está malformado
    """
    ...

# ❌ Mal
def extract_normativa(html_content, municipality):
    ...
```

### Git Commits

Seguimos [Conventional Commits](https://www.conventionalcommits.org/):

```
<tipo>(<scope>): <descripción corta>

[cuerpo opcional]

[footer opcional]
```

**Tipos válidos:**
- `feat`: Nueva funcionalidad
- `fix`: Corrección de bug
- `docs`: Cambios en documentación
- `style`: Formateo (sin cambios lógicos)
- `refactor`: Refactorización
- `perf`: Mejoras de performance
- `test`: Agregar/modificar tests
- `chore`: Tareas de mantenimiento
- `build`: Cambios en build
- `ci`: Cambios en CI/CD

**Ejemplos:**

```bash
# ✅ Bien
git commit -m "feat(chat): agregar filtro por rango de fechas"
git commit -m "fix(scraper): corregir parsing de tablas con colspan"
git commit -m "docs: actualizar README con nuevos municipios"

# ❌ Mal
git commit -m "cambios"
git commit -m "fix bug"
git commit -m "WIP"
```

---

## 🔢 Sistema de Versionado

Usamos [Semantic Versioning](https://semver.org/):

```
MAJOR.MINOR.PATCH
```

- **MAJOR**: Breaking changes (ej: 1.x.x → 2.0.0)
- **MINOR**: Nuevas funcionalidades (ej: 1.1.x → 1.2.0)
- **PATCH**: Bug fixes (ej: 1.1.1 → 1.1.2)

**Versionado Automático:** Este proyecto usa **Release Please** que calcula automáticamente la versión correcta basándose en tus commits. No necesitas calcular manualmente qué versión corresponde.

Ver:
- [docs/AUTOMATED_RELEASES.md](docs/AUTOMATED_RELEASES.md) - Sistema automático
- [docs/VERSIONING.md](docs/VERSIONING.md) - Manual completo

---

## 🐛 Reportar Bugs

### Antes de Reportar

1. **Busca issues existentes**: Puede que ya esté reportado
2. **Verifica que sea reproducible**: Intenta reproducir en un entorno limpio
3. **Recopila información**: Versión, navegador, OS, logs, screenshots

### Crea un Issue

Usa el template [Bug Report](.github/ISSUE_TEMPLATE/bug_report.md):

1. Ve a [Issues](https://github.com/mrtn/sibom-scraper-assistant/issues/new/choose)
2. Selecciona "🐛 Reporte de Bug"
3. Completa toda la información solicitada
4. Espera feedback (responderé en 24-48 horas)

---

## ✨ Sugerir Funcionalidades

### Antes de Sugerir

1. **Verifica que no exista**: Revisa issues y PRs abiertos
2. **Considera el alcance**: ¿Es consistente con el propósito del proyecto?
3. **Piensa en alternativas**: ¿Hay otras formas de lograr lo mismo?

### Crea un Feature Request

Usa el template [Feature Request](.github/ISSUE_TEMPLATE/feature_request.md):

1. Ve a [Issues](https://github.com/mrtn/sibom-scraper-assistant/issues/new/choose)
2. Selecciona "✨ Feature Request"
3. Describe claramente el problema que resuelve
4. Propone una solución detallada
5. Estima el impacto y prioridad

---

## 🚀 Proceso de Review

### Qué esperar

1. **Respuesta inicial**: 24-48 horas
2. **Review completo**: 3-7 días (dependiendo de la complejidad)
3. **Iteraciones**: Puede haber varios rounds de feedback
4. **Merge**: Una vez aprobado, se mergea y se incluye en el próximo release

### Criterios de Aprobación

- ✅ Tests pasan
- ✅ Build exitoso
- ✅ Código sigue convenciones
- ✅ Documentación actualizada
- ✅ Sin reducción de performance
- ✅ Sin introducción de vulnerabilidades
- ✅ Commits bien formateados

---

## 📚 Recursos Útiles

### Documentación del Proyecto

- [README.md](README.md) - Overview del proyecto
- [docs/VERSIONING.md](docs/VERSIONING.md) - Sistema de versionado
- [CHANGELOG.md](CHANGELOG.md) - Historial de cambios
- [.agents/README.md](.agents/README.md) - Arquitectura completa

### Herramientas

- [Convencional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [GitHub Flow](https://guides.github.com/introduction/flow/)

### Comunidad

- GitHub Issues: Para bugs y features
- GitHub Discussions: Para preguntas y discusiones generales
- Email: [tu-email] - Para consultas privadas

---

## ❓ FAQ

### ¿Puedo trabajar en un issue sin asignación previa?

Sí, pero comenta en el issue primero para evitar duplicar trabajo.

### ¿Cuánto tiempo toma que aprueben mi PR?

Generalmente 3-7 días. Para urgentes, menciona en el PR.

### ¿Puedo hacer PRs grandes?

Preferiblemente no. Divide en PRs más pequeños para facilitar el review.

### ¿Qué pasa si mi PR es rechazado?

No te desanimes. Recibirás feedback claro de por qué y cómo mejorarlo.

### ¿Puedo recibir pagos por contribuciones?

No en este momento. Todas las contribuciones son voluntarias.

---

## 🙏 Agradecimientos

¡Gracias por contribuir a SIBOM IA!

Tu tiempo y esfuerzo ayudan a hacer este proyecto mejor para todos.

---

**Última actualización:** 2026-02-14  
**Mantenedor:** @mrtn  
**Versión de esta guía:** 1.0
