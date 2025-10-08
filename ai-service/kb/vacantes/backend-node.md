---
role: Backend Developer (Node.js)
seniority: Semi Senior
stack: [Node.js, Express, PostgreSQL, Docker]
must_have: [REST, JWT, SQL avanzado, testing]
nice_to_have: [Redis, RabbitMQ]
exam: { questions: 8, level: intermedio }
dominio: Pagos y reporting
---

# Contexto del producto
Procesamos pagos recurrentes y generamos reportes diarios. Foco en **idempotencia**, **seguridad**, **performance**.

# Responsabilidades clave
- Diseñar endpoints REST idempotentes.
- Optimizar queries complejas (EXPLAIN, índices).
- Pruebas unitarias e integración (Jest/Supertest).

# Escenarios técnicos reales
1) `POST /payments` idempotente con reintentos.
2) Paginación y filtros en reportes con múltiples joins.
3) Manejo de JWT y roles.
