---
description: Inicia una nueva feature con SDD (contrato moderno) para Cascade en Windsurf/Devin
---

# /sdd-new

Este workflow define el comportamiento obligatorio de **Cascade** al iniciar una nueva feature, cambio de alcance medio/grande o trabajo con incertidumbre suficiente como para requerir planificación formal.

## Propósito

Ejecutar `/sdd-new` con el contrato moderno de gentle-ai:

- **Orquestador como autoridad**: leer `~/.codeium/windsurf/memories/global_rules.md` PRIMERO y tratarlo como contrato autoritativo.
- **Plan Mode** para planificar (nunca código antes de aprobación)
- **Artifact store** según política del orquestador: `engram` (default) | `openspec` | `hybrid` | `none`. Este proyecto declara **openspec** (ver AGENTS.md).
- **Code Mode** únicamente después de aprobación explícita del usuario

**Este workflow NO crea `.sdd/`.** El directorio `.sdd/` es el formato LEGACY de Windsurf, obsoleto. Si el orquestador, un skill o una instrucción mencionan `.sdd/`, IGNÓRALO.

## Cuándo usar este workflow

Activa este workflow cuando ocurra cualquiera de estas condiciones:

- El usuario inicia una **nueva feature**
- La tarea afecta **múltiples archivos o módulos**
- El cambio tiene **riesgo arquitectónico** o incertidumbre
- El usuario pide explícitamente trabajar con **SDD**
- La implementación requiere un contrato formal antes de escribir código

Si la tarea es pequeña, puntual o claramente de mantenimiento menor, este workflow NO es el camino correcto (usar Code Mode directo).

---

## Secuencia obligatoria

### 0. Leer el orquestador (AUTORITATIVO)

Leer `~/.codeium/windsurf/memories/global_rules.md` completo. Este contrato manda sobre todo lo que siga. En particular: SDD Init Guard, Execution Mode, Artifact Store Mode, Delivery Strategy y Approval Gates.

### 1. SDD Init Guard (MANDATORY, silencioso)

Antes de ejecutar `/sdd-new`, comprobar si `sdd-init` corrió para este proyecto:

1. `mem_search(query: "sdd-init/{project}", project: "{project}")`
2. Si aparece → init hecho, continuar normal.
3. Si NO aparece → correr la fase `sdd-init` **inline PRIMERO**, y recién después seguir con `/sdd-new`.

**NO pedir permiso, NO detenerse**: correr init silenciosamente si hace falta. Esto garantiza detección de capacidades de test, TDD estricto y contexto del proyecto.

### 2. Determinar y cachear opciones de sesión

La primera vez en la sesión, resolver y cachear:

- **Execution Mode**: preguntar `Automatic` (default) vs `Interactive`. En Windsurf, `Interactive` es el comportamiento natural vía Approval Gates; `Automatic` omite los gates y corre todo secuencial.
- **Artifact Store Mode**: preguntar `engram` | `openspec` | `hybrid` | `none`. Si el usuario no especifica, detectar: engram disponible → `engram`; si no → `none`. **Este proyecto declara `openspec`** en AGENTS.md, así que la elección debe partir de ahí.
- **Delivery Strategy**: preguntar `ask-on-risk` (default) | `auto-chain` | `single-pr` | `exception-ok`.

Cachear las tres para la sesión. No preguntar de nuevo salvo pedido explícito.

### 3. Entrar en Plan Mode

Entrar en **Plan Mode** de inmediato. Analizar el pedido, formular el plan de alto nivel, identificar alcance, riesgos, dependencias y archivos probables.

Prohibido en esta etapa:

- NO escribir código de producción
- NO entrar en Code Mode
- NO modificar lógica de la aplicación
- NO ejecutar implementación parcial "para adelantar trabajo"
- NO asumir aprobación implícita

### 4. Recuperar contexto

Antes de redactar cualquier artefacto SDD, recuperar contexto arquitectónico y restricciones del proyecto:

1. **Engram** vía MCP: `mem_search` para decisiones previas y `mem_context` para contexto reciente
2. Leer el orquestador (`global_rules.md`) si aún no está en contexto
3. Leer `AGENTS.md` del proyecto
4. Cargar los skills SDD de `~/.codeium/windsurf/skills/sdd-*/SKILL.md` cuando la fase los requiera

Buscar, como mínimo: decisiones arquitectónicas previas, convenciones del repo, restricciones, reglas de calidad, patrones establecidos.

Si no hay contexto suficiente, decirlo explícitamente en el plan. **No inventar convenciones.**

### 5. Fase explore (inline)

Ejecutar la fase `sdd-explore` inline: investigar el codebase para este cambio, comparar enfoques, sin crear archivos. Guardar el artifact `explore` en el store activo:

- **engram**: topic key `sdd/{change-name}/explore`
- **openspec**: `openspec/changes/<change-name>/exploration.md`

Presentar el resumen de exploración al usuario.

### 6. Fase propose (inline)

Ejecutar la fase `sdd-propose` inline para crear el proposal a partir de la exploración. Guardar el artifact `proposal` en el store activo:

- **engram**: topic key `sdd/{change-name}/proposal`
- **openspec**: `openspec/changes/<change-name>/proposal.md`

Usar el nombre del cambio pasado por el usuario (`$ARGUMENTS`). Si no se indicó nombre, proponer uno en kebab-case y confirmarlo.

#### Contenido mínimo del proposal

- Título del cambio
- Problema a resolver
- Objetivo
- Alcance incluido / excluido
- Enfoque propuesto
- Riesgos principales
- Supuestos abiertos
- Preguntas o decisiones pendientes

**NO crear `.sdd/` ni `.sdd/proposal.md` ni `.sdd/spec.md` bajo ninguna circunstancia.**

### 7. Presentar resumen y Approval Gate

Presentar un resumen breve del proposal (objetivo, alcance, riesgos) y detenerse **ABSOLUTAMENTE**.

Preguntar exactamente:

**¿Apruebas este plan de implementación?**

- Esperar confirmación explícita (sí / aprobado / de acuerdo / go ahead / equivalente)
- NO continuar a Code Mode sin aprobación
- NO interpretar silencio como aprobación
- Si el usuario pide cambios: ajustar el proposal, volver a presentar, volver a preguntar

### 8. Después de la aprobación

Con el proposal aprobado, continuar con las fases restantes (`spec`, `design`, `tasks`) vía `/sdd-continue` o `/sdd-ff`, según Execution Mode. Solo entonces, y con approval gate superado, pasar a Code Mode para `apply`.

---

## Prohibiciones explícitas

Mientras este workflow no haya sido aprobado por el usuario:

- NO escribir código de producción
- NO editar archivos de implementación
- NO ejecutar tareas de aplicación
- NO cambiar a Code Mode
- NO crear commits
- NO correr una implementación parcial
- NO continuar automáticamente al siguiente paso de SDD
- NO crear el directorio `.sdd/` ni sus artefactos (formato legacy obsoleto)

---

## Criterio de salida de este workflow

Este workflow se considera correctamente ejecutado solo si:

- Leyó el orquestador (`global_rules.md`) como autoridad
- Aplicó el SDD Init Guard (corriendo `sdd-init` inline y silencioso si faltaba)
- Resolvió y cacheó Execution Mode, Artifact Store Mode y Delivery Strategy
- Usó **Plan Mode**
- Recuperó contexto con **Engram**, el orquestador o `AGENTS.md`
- Ejecutó `sdd-explore` y `sdd-propose` inline en ese orden
- Guardó el proposal en el store activo (este proyecto: `openspec/changes/<name>/proposal.md`)
- Presentó el resumen y preguntó exactamente: **¿Apruebas este plan de implementación?**
- Se detuvo a esperar aprobación explícita
- NO creó `.sdd/` en ningún momento

Si cualquiera de esos puntos no ocurre, el workflow está mal ejecutado.
