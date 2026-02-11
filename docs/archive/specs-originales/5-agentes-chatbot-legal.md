# 5 Agentes de Diseño - Chatbot Legal Municipal

> **Objetivo:** Crear un chatbot de información legal municipal que destaque por su calidad UX, sea único y no "otro chat más".

---

## 🤖 Agente 1: Elena - Experta en Accesibilidad Urbana

### Perspectiva: "El ciudadano promedio no es un experto en tecnología"

**Diagnóstico:**
> "El 70% de los usuarios que buscan información legal municipal tienen entre 35-65 años, muchos no dominan interfaces complejas. Necesitamos diseñar para el ciudadano común, no para un tech-savvy millennial."

### Propuestas UX:

#### 1. **Modo Conversación Natural con Escucha Activa**
```typescript
// No preguntas, sino confirmaciones activas
const conversationStyles = {
  // En lugar de: "¿Buscas información sobre?"
  // Usar: "Entiendo que quieres saber sobre..."
  
  confirmBeforeSearch: true,
  autoSummarize: true,
  progressiveDisclosure: true
}
```

**Implementación:**
- El bot reformula la pregunta del usuario antes de buscar: *"Entiendo que quieres saber sobre multas de tránsito en La Plata. ¿Es correcto?"*
- Muestra un resumen de la conversación antes de dar la respuesta final
- Permite retroceder en cualquier momento con frases naturales: *"No, me refería a otra cosa"*

#### 2. **Búsqueda por Voz con方言 Support**
- Incorporar reconocimiento de voz con soporte para acentos argentinos
- Feedback visual inmediato mientras escucha
- Transcripción editable si detectó algo mal

#### 3. **Zona de Confort Visual**
```
┌─────────────────────────────────────────────────────────┐
│  🔴 Nochat Minimalista                                   │
│  ─────────────────────────────────────────────────────  │
│  "Hola Martín,¿En qué puedo ayudarte hoy?"              │
│                                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │ 🎤 "Cómo puedo pagar mi patente"               │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│  [Respuesta clara con pasos numerados]                  │
│  [Botón: "¿Esto resolvió tu duda?"]                     │
│                                                         │
│  [FAQ Cacheadas: "¿Cómo inscribo mi comercio?"...]      │
└─────────────────────────────────────────────────────────┘
```

**Reglas UX:**
- **Maximum 3 opciones visibles** a la vez
- ** Colores de alto contraste** para textos legales
- **Tamaños de fuente** ajustables con control visible
- **Ayuda contextual** que no invade el espacio

#### 4. **Navegación por Tarjetas de Información**
```
┌──────────────────────┐  ┌──────────────────────┐
│ 📋 ORDENANZA         │  │ 📋 DECRETO           │
│ ───────────────────  │  │ ───────────────────  │
│ #4523/2024           │  │ #892/2024            │
│ ▸ Ver resumen        │  │ ▸ Ver resumen        │
│ ▸ Descargar PDF      │  │ ▸ Descargar PDF      │
│ ▸ Municipios aplica  │  │ ▸ Municipios aplica  │
└──────────────────────┘  └──────────────────────┘
```

**Patrón de diseño:** Cardsinfo-tiles con información crítica visible sin expandir.

---

## 🤖 Agente 2: Marcos - Arquitecto de Información

### Perspectiva: "La estructura es la skeletoni del éxito"

**Diagnóstico:**
> "La información legal municipal es un laberinto. El bot no debe ser otro nivel de abstracción, sino un GPS claro."

### Propuestas UX:

#### 1. **Taxonomía Visual del Conocimiento**
```
                    ┌──────────────────┐
                    │  🏛️Información   │
                    │    LEGAL         │
                    └────────┬─────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ 📜 ORDENANZAS │   │ 📑 DECRETOS   │   │ 📋 EDICTOS    │
│               │   │               │   │               │
│ • Tributarias │   │ • Generales   │   │ • Normativas  │
│ • Seguridad   │   │ • Específicos │   │ • Comunicados │
│ • Urbanismo   │   │ • Emergencia  │   │ • Licitaciones│
└───────────────┘   └───────────────┘   └───────────────┘
```

**Interfaz de navegación:**
- **Sidebar colapsable** con icons grandes
- **Breadcrumbs** visibles en cada pantalla
- **Árbol de categorías** con expansión progresiva

#### 2. **Smart Context Engine**
```typescript
interface ContextEngine {
  // El bot "recuerda" el hilo de conversación
  conversationHistory: ContextWindow;
  
  // Detecta cambios de tema automáticamente
  topicTransitionDetection: {
    enabled: true,
    threshold: 0.7 // 70% de certeza para cambio de tema
  };
  
  // Sugerencias contextuales basadas en navegación
  contextualSuggestions: [
    "📎 Documentos relacionados",
    "🔗 Boletines similares", 
    "📍 Municipios con norma similar"
  ];
}
```

**UX Flow:**
1. Usuario pregunta sobre "multas de tránsito"
2. Bot detecta contexto: `topic=traffic_violations`, `municipio=current`
3. Muestra resumen + documentos relacionados + municipios con normativa similar

#### 3. **Timeline Legal Interactivo**
```
┌──────────────────────────────────────────────────────────┐
│  EVOLUCIÓN NORMATIVA: tasas municipales (2020-2025)      │
│                                                          │
│  2020  ────●─────●─────●─────●─────●─────●─────●─── 2025 │
│           │     │     │     │     │     │     │     │   │
│        [O20] [O35] [O48] [O52] [D15] [O61] [O73] [O85]  │
│        Tax     Tax   Tax   Tax   Emer  Tax   Tax   Tax  │
│        Ref     Ref   Ref   Ref   gency Ref   Ref   Ref  │
│                                                          │
│  [Ver evolución completa] [Filtrar por año]              │
└──────────────────────────────────────────────────────────┘
```

**Valor diferencial:** Mostrar cómo evolucionó una normativa, no solo el estado actual.

---

## 🤖 Agente 3: Lucía - Diseñadora de Interacción Conversacional

### Perspectiva: "Cada palabra cuenta, cada segundo importa"

**Diagnóstico:**
> "Los chats legales típicos son secos, roboticos, y frustrantes. Necesitamos personalidad sin perder profesionalismo."

### Propuestas UX:

#### 1. **Personalidad del Bot Configurable**
```typescript
const botPersonality = {
  // Nivel de formalidad: 1 (formal) - 5 (amigable)
  formalityLevel: 3, 
  
  // Tono emocional
  tone: {
    empathy: true,
    reassurance: true,
    clarity: "high",
    confidence: "very-high"
  },
  
  // Respuestas personalizadas
  greetings: {
    morning: "¡Buenos días! 🌞",
    afternoon: "¡Buenas tardes!",
    evening: "¡Buenas noches!",
    returning: "¡Volviste! ¿En qué te ayudo hoy?"
  }
};
```

**Personalidades por perfil:**
| Perfil | Tono | Ejemplo de apertura |
|--------|------|---------------------|
| Formal | Profesional | "¿En qué puedo asistirlo?" |
| Neutro | Cercano | "¿En qué te puedo ayudar?" |
| Amigable | Caluroso | "¡Hola! ¿Cómo estás hoy?" |

#### 2. **Sistema de Feedback Emocional**
```
┌─────────────────────────────────────────────────────────┐
│  🗣️ "Según la Ordenanza 4523, los contribuyentes..."  │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │  ¿Te fue útil esta respuesta?                   │   │
│  │                                                 │   │
│  │  😊 Sí, gracias    🤔 Meh    ❌ No, no entendí │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  [Si "Meh" o "No"] → "¿Qué parte no fue clara?"       │
│  → Desglose automático de la respuesta                 │
└─────────────────────────────────────────────────────────┘
```

**UX micro-interactions:**
- **Typing indicators** con mensajes breves del proceso
- **Progress bars** para búsquedas complejas
- **Success states** con animaciones sutiles (no molestas)

#### 3. **Respuestas "Cascada" para Complejidad Legal**
```
┌─────────────────────────────────────────────────────────┐
│  📋 RESPUESTA COMPLETA                                 │
│  ─────────────────────────────────────────────────────  │
│  ┌─ Ver respuesta corta (2 líneas)                     │
│  │                                                       │
│  │  La tasa de publicidad y propaganda se abate un      │
│  │  20% para comerciantes locales.                     │
│  │                                                       │
│  └─ [📖 Ver respuesta completa]                        │
│                                                         │
│  ┌─ Ver explicación (5 líneas)                         │
│  │                                                       │
│  │  Según Ordenanza 4523/2024, Artículo 15:            │
│  │  Los comerciantes con local físico en el            │
│  │  municipio tienen derecho a un abate del...         │
│  │                                                       │
│  └─ [📑 Ver detalles técnicos + referencias]           │
└─────────────────────────────────────────────────────────┘
```

**Progressive disclosure** es clave para no abrumar.

---

## 🤖 Agente 4: Diego - Estratega de Contenido Legal

### Perspectiva: "El contenido es el rey, pero el contexto es Dios"

**Diagnóstico:**
> "Copiar texto legal no es suficiente. El ciudadano necesita entender qué significa PARA ÉL."

### Propuestas UX:

#### 1. **Engine de Traducción Legal→Ciudadano**
```typescript
interface LegalSimplifier {
  // Pipeline de simplificación
  pipeline: [
    "extract_core_meaning",      // Extraer significado central
    "identify_implications",     // Identificar implicancias prácticas
    "generate_examples",         // Generar ejemplos concretos
    "list_requirements",         // Listar requisitos/documentos necesarios
    "provide_contacts"           // Proporcionar contactos útiles
  ];
  
  // Output estructurado
  outputStructure: {
    summary: string;      // 1-2 líneas
    whatMeans: string;    // Explicación simple
    example: string;      // Caso de uso real
    requirements: string[]; // Lista de qué necesitas
    steps: string[];      // Pasos a seguir
    sources: string[];    // Referencias legales
  };
}
```

**Ejemplo de transformación:**
```
❌ Original legal:
"Conforme artículo 42, Ord. 4523/24, los sujetos obligados al pago
de la Tasa de Inspección de Seguridad e Higiene deberán presentar
declaración jurada mensual dentro de los quince días hábiles 
siguientes al mes vencido, bajo apercibimiento de aplicar 
multas coercitivas..."

✅ Versión ciudadana:
┌─────────────────────────────────────────────────────────┐
│  📋 TASA DE COMERCIO - LO QUE DEBÉS SABER              │
│  ─────────────────────────────────────────────────────  │
│                                                         │
│  🔑 Resumen:                                            │
│  Si tenés un comercio, pagás tasa mensual.              │
│                                                         │
│  💡 ¿Qué significa en la práctica?                      │
│  Cada mes debés declarar cuánto vendiste y pagar         │
│  un porcentaje (varía según tu actividad).              │
│                                                         │
│  📋 Requisitos:                                         │
│  • Número de CUIT                                       │
│  • Declaración de ventas mensual                        │
│  • Formulario AFIP (si aplica)                          │
│                                                         │
│  📅 Fechas importantes:                                 │
│  • Deadline: 15 de cada mes                             │
│  • Pago: Dentro de los 15 días del mes siguiente        │
│                                                         │
│  📞 ¿Dudas?                                             │
│  • Tel: 0221-456-7890                                   │
│  • Email: tasas@municipiolaplata.gob.ar                 │
│                                                         │
│  📄 Fuente: Ord. 4523/24, Art. 42                      │
└─────────────────────────────────────────────────────────┘
```

#### 2. **Selector de Escenarios por Persona**
```
┌─────────────────────────────────────────────────────────┐
│  🔍 FILTRAR POR TU SITUACIÓN                            │
│  ─────────────────────────────────────────────────────  │
│                                                         │
│  👤 Soy un ciudadano buscando...                        │
│     ○ Información general sobre tasas                   │
│     ○ Cómo inscribir mi negocio                         │
│     ○ Multas y cómo apelarlas                           │
│     ○ Permisos de construcción                          │
│     ○ Otro...                                           │
│                                                         │
│  🏢 Soy comerciante con...                              │
│     ○ Local físico                                      │
│     ○ Comercio online                                   │
│     ○ Restaurant/Bar                                    │
│     ○ Otro...                                           │
│                                                         │
│  🏗️ Estoy por abrir...                                  │
│     ○ Comercio minorista                                │
│     ○ Servicio profesional                              │
│     ○ Industria                                         │
│     ○ Otro...                                           │
└─────────────────────────────────────────────────────────┘
```

**UX Diferencial:** Las respuestas se adaptan al perfil del usuario desde el inicio.

#### 3. **Comparador de Municipios**
```
┌──────────────────────────────────────────────────────────┐
│  📊 Comparativa: Tasa Comercial (2024)                   │
│                                                          │
│  ┌──────────┬──────────────┬──────────────┬────────────┐ │
│  │ Municipio│ Tasa básica  │ Bonificación │ Vencimiento│ │
│  ├──────────┼──────────────┼──────────────┼────────────┤ │
│  │ La Plata │ 2.5%         │ 20% local    │ 15/mensual │ │
│  │ Merlo    │ 3.0%         │ 10% PyMEs    │ 20/mensual │ │
│  │  Junín   │ 2.0%         │ 30% industria│ 10/mensual │ │
│  └──────────┴──────────────┴──────────────┴────────────┘ │
│                                                          │
│  [Ver comparación completa] [Filtrar por zona]          │
└──────────────────────────────────────────────────────────┘
```

**Valor único:** Información comparativa que no existe en otros lados.

---

## 🤖 Agente 5: Sofia - Arquitecta de Datos y Confianza

### Perspectiva: "Sin confianza, no hay uso. Sin precisión, no hay confianza."

**Diagnóstico:**
> "La información legal es sensible. Un error puede costar dinero o problemas legales. La confianza es nuestra moneda principal."

### Propuestas UX:

#### 1. **Sistema de Transparencia Total**
```typescript
interface TransparencySystem {
  // Siempre mostrar fuente
  showSources: true,
  
  // Marcar nivel de certeza
  confidenceLevel: {
    high: "✅ Respuesta clara en la norma",
    medium: "⚠️ Interpretación necesaria",
    low: "❓ Información incompleta"
  },
  
  // Disclaimer proactivo
  disclaimers: {
    showBeforeResponse: true,
    showOnComplexTopics: true,
    customizableByUser: true
  }
}
```

**UI de Confianza:**
```
┌──────────────────────────────────────────────────────────┐
│  ✅ INFORMACIÓN VERIFICADA                               │
│  ─────────────────────────────────────────────────────   │
│                                                          │
│  📄 Fuente: Ordenanza 4523/2024 - Municipality La Plata │
│  📅 Fecha Publicación: 15/03/2024                        │
│  🔗 [Ver Boletín Original] [Ver histórico de cambios]    │
│                                                          │
│  ⚠️ Nota: Esta información está actualizada a dic/2025. │
│     Verifica en la municipalía antes de actuar.          │
│                                                          │
│  🤖 Respuesta generada con IA. ¿Algo parece incorrecto?  │
│     [Reportar error] [Ver cómo funciona]                 │
└──────────────────────────────────────────────────────────┘
```

#### 2. **Cache FAQ con Refresh Inteligente**
```typescript
interface FAQSystem {
  // FAQs cacheadas con TTL
  cache: {
    ttl: 3600, // 1 hora
    refreshStrategy: "background",
    invalidation: ["new_bulletin", "user_feedback"]
  },
  
  // Tags de confiabilidad
  metadata: {
    lastVerified: Date,
    verifiedBy: "legal_team" | "automated",
    citationCount: number
  },
  
  // Búsqueda semántica
  search: {
    fuzzyMatch: true,
    synonymHandling: true,
    contextAware: true
  }
}
```

**UX:**
- FAQs siempre instantáneas (del cache)
- Indicador de última verificación visible
- Botón "Actualizar" discreto que no interrumpe

#### 3. **Historial de Conversaciones Persistente**
```
┌──────────────────────────────────────────────────────────┐
│  📚 MIS CONSULTAS ANTERIORES                             │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │ 📅 15/12/2024 - "Tasa de comercio La Plata"       │  │
│  │    [Ver respuesta] [Ver normativa] [Guardar PDF]  │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │ 📅 02/11/2024 - "Cómo apelar multa de tránsito"   │  │
│  │    [Ver respuesta] [Ver normativa] [Guardar PDF]  │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  [Ver todas] [Exportar historial]                        │
└──────────────────────────────────────────────────────────┘
```

**Features:**
- Exportar a PDF para tener registro
- Recordatorios opcionales de renovación de trámites
- Compartir con profesionales (abogados/contadores)

#### 4. **Modo Profesional (Toggle)**
```
┌──────────────────────────────────────────────────────────┐
│  ⚙️ MODO: [Ciudadano] | [Profesional]                   │
│                                                          │
│  MODO CIUDADANO:                                         │
│  "Según la Ordenanza 4523, los comerciantes..."         │
│  + Resumen simple + Pasos a seguir                      │
│                                                          │
│  ─────────────────────────────────────────────────────   │
│                                                          │
│  MODO PROFESIONAL (abogados/contadores):                │
│  "Ord. 4523/24, Art. 15, inc. b): Tasa de Inspección    │
│  de Seguridad e Higiene. Base imponible: facturación.   │
│  Alícuota 2.5% para actividades comerciales.            │
│  + Texto completo + Jurisprudencia + Normativa related  │
└──────────────────────────────────────────────────────────┘
```

**UX Diferencial:** Mismo contenido, presentación adaptada al usuario.

---

## 🎯 Síntesis: Los 5 Pilares UX Distintivos

| Agente | Pilar | Característica Única |
|--------|-------|---------------------|
| **Elena** | Accesibilidad | Modo voz + diseño para no-digitales |
| **Marcos** | Arquitectura | Timeline legal + contexto smart |
| **Lucía** | Conversación | Personalidad + feedback emocional |
| **Diego** | Contenido | Traducción legal→ciudadano + escenarios |
| **Sofía** | Confianza | Transparencia total + modo profesional |

---

## 🚀 Recomendaciones de Implementación

### Fase 1 (MVP - 4 semanas)
1. ✅ Sistema de FAQ cacheadas con search semántico
2. ✅ UI limpia con Progressive Disclosure
3. ✅ Fuentes visibles en cada respuesta
4. ✅ Modo toggle (Ciudadano/Profesional)

### Fase 2 (Mes 2)
1. 🎯 Búsqueda por voz con acentos
2. 🎯 Timeline de evolución normativa
3. 🎯 Comparador de municipios
4. 🎯 Historial persistente

### Fase 3 (Mes 3+)
1. 🌟 Personalidad configurable del bot
2. 🌟 Modo conversación natural con confirmación
3. 🌟 Sistema de feedback emocional
4. 🌟 Integración con trámites digitales

---

## ❓ Preguntas para el equipo

1. **Recursos disponibles:** ¿Cuántas personas trabajarán en el frontend vs backend?
2. **Timeline real:** ¿4 semanas para MVP es realista o muy ambicioso?
3. **Integraciones:** ¿Hay APIs de municipalidades para información en tiempo real?
4. **Presupuesto:** ¿Tenemos presupuesto para servicios premium de AI o usamos open source?
5. **Legal:** ¿Alguien del equipo legal validará las respuestas automáticas?

---

> **Documento creado:** 31/12/2024  
> **Versión:** 1.0  
> **Próximo paso:** Revisar con stakeholders y priorizar features
