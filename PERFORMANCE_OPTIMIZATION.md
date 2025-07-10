# Guia de Otimização de Performance - CrmSalao

## 🚀 Análise de Performance Atual

### Métricas do Sistema

**Estatísticas do Código:**
- **Total de Linhas**: ~2,586 linhas Python
- **Arquivos de Template**: 14 templates Jinja2
- **Endpoints de API**: ~25+ endpoints
- **Modelos de Dados**: 5 principais (Cliente, Profissional, Serviço, Agendamento, AppSetting)

### Gargalos Identificados

#### 1. **Database Queries** (Impacto Alto)

**Problema**: Queries N+1 em várias operações

**Arquivo**: `app/routers/n8n_api/agendamentos.py` (linhas 320-322)
```python
# ❌ PROBLEMA: N+1 Queries
for agendamento in agendamentos:
    servicos = db.query(Servico).filter(Servico.id.in_(agendamento.servicos)).all()
    profissional = db.query(Profissional).filter(Profissional.id == agendamento.profissional_id).first()
```

**Impacto**: 
- Múltiplas queries para cada agendamento
- Tempo de resposta aumenta exponencialmente
- Sobrecarga no banco de dados

#### 2. **Cache Ausente** (Impacto Médio)

**Problema**: Dados estáticos consultados repetidamente

**Exemplos**:
- Lista de serviços
- Horários de profissionais
- Configurações do sistema

#### 3. **Falta de Paginação** (Impacto Médio)

**Problema**: Carregamento completo de listas grandes

**Arquivo**: Dashboard queries sem limitação
```python
# ❌ PROBLEMA: Carrega todos os registros
agendamentos = db.query(Agendamento).all()
```

## 🔧 Plano de Otimização

### Fase 1: Otimização de Database (Prioridade Alta)

#### 1.1 Eager Loading com SQLAlchemy

**Solução**: Usar `joinedload` e `selectinload`

```python
# ✅ SOLUÇÃO: Eager Loading
from sqlalchemy.orm import joinedload, selectinload

# Antes (N+1 queries)
agendamentos = db.query(Agendamento).all()
for agendamento in agendamentos:
    cliente = db.query(Cliente).get(agendamento.cliente_id)
    profissional = db.query(Profissional).get(agendamento.profissional_id)

# Depois (1 query)
agendamentos = db.query(Agendamento)\
    .options(
        joinedload(Agendamento.cliente),
        joinedload(Agendamento.profissional)
    ).all()
```

#### 1.2 Índices de Banco de Dados

**Criar migration para índices:**

```python
# alembic/versions/add_performance_indexes.py
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Índices para queries frequentes
    op.create_index('idx_agendamentos_cliente_id', 'agendamentos', ['cliente_id'])
    op.create_index('idx_agendamentos_profissional_id', 'agendamentos', ['profissional_id'])
    op.create_index('idx_agendamentos_start_date', 'agendamentos', ['start'])
    op.create_index('idx_agendamentos_status', 'agendamentos', ['status'])
    
    # Índice composto para queries comuns
    op.create_index('idx_agendamentos_date_status', 'agendamentos', ['start', 'status'])
    
    # Índices para busca de clientes
    op.create_index('idx_clientes_phone', 'clientes', ['phone'])
    op.create_index('idx_clientes_email', 'clientes', ['email'])
```

#### 1.3 Query Optimization

**Arquivo**: `app/repositories/agendamento_repository.py`

```python
# ✅ REPOSITÓRIO OTIMIZADO
class AgendamentoRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_agendamentos_by_date_range(self, start_date: date, end_date: date):
        """Busca agendamentos com joins otimizados"""
        return self.db.query(Agendamento)\
            .options(
                joinedload(Agendamento.cliente),
                joinedload(Agendamento.profissional)
            )\
            .filter(
                Agendamento.start >= start_date,
                Agendamento.start <= end_date
            )\
            .order_by(Agendamento.start)\
            .all()
    
    def get_dashboard_stats(self):
        """Estatísticas em uma única query"""
        from sqlalchemy import func
        
        result = self.db.query(
            func.count(Agendamento.id).label('total_agendamentos'),
            func.count(case([(Agendamento.status == 'agendado', 1)])).label('agendamentos_ativos'),
            func.sum(case([(Agendamento.status == 'concluido', 1)], else_=0)).label('agendamentos_concluidos')
        ).first()
        
        return {
            'total_agendamentos': result.total_agendamentos,
            'agendamentos_ativos': result.agendamentos_ativos,
            'agendamentos_concluidos': result.agendamentos_concluidos
        }
```

### Fase 2: Implementação de Cache (Prioridade Média)

#### 2.1 Redis Cache Setup

**Arquivo**: `app/cache/redis_client.py`

```python
# ✅ IMPLEMENTAÇÃO DE CACHE
import redis
import json
from typing import Any, Optional
from datetime import timedelta

class RedisCache:
    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0):
        self.client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
    
    def get(self, key: str) -> Optional[Any]:
        """Busca valor no cache"""
        try:
            value = self.client.get(key)
            return json.loads(value) if value else None
        except:
            return None
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        """Armazena valor no cache"""
        try:
            self.client.setex(key, ttl, json.dumps(value, default=str))
            return True
        except:
            return False
    
    def delete(self, key: str):
        """Remove valor do cache"""
        return self.client.delete(key)

# Instância global
cache = RedisCache()
```

#### 2.2 Cache Decorators

**Arquivo**: `app/cache/decorators.py`

```python
# ✅ DECORADORES DE CACHE
from functools import wraps
from .redis_client import cache

def cached(ttl: int = 3600, key_prefix: str = ""):
    """Decorator para cache automático"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Gerar chave única
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Tentar buscar no cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Executar função e armazenar no cache
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator

# Uso
@cached(ttl=1800, key_prefix="servicos")
def get_all_servicos():
    return db.query(Servico).all()
```

#### 2.3 Cache Strategy para Dados Específicos

```python
# ✅ ESTRATÉGIAS DE CACHE
class CacheManager:
    
    @staticmethod
    def get_servicos_profissional(profissional_id: int):
        """Cache para serviços de profissional"""
        cache_key = f"servicos_profissional:{profissional_id}"
        cached = cache.get(cache_key)
        
        if cached:
            return cached
        
        # Buscar no banco
        profissional = db.query(Profissional).get(profissional_id)
        servicos = db.query(Servico).filter(Servico.id.in_(profissional.services)).all()
        
        # Armazenar no cache por 1 hora
        cache.set(cache_key, servicos, 3600)
        return servicos
    
    @staticmethod
    def invalidate_profissional_cache(profissional_id: int):
        """Invalida cache quando profissional é atualizado"""
        cache.delete(f"servicos_profissional:{profissional_id}")
```

### Fase 3: Paginação e Limitação (Prioridade Média)

#### 3.1 Paginação Padrão

**Arquivo**: `app/utils/pagination.py`

```python
# ✅ SISTEMA DE PAGINAÇÃO
from sqlalchemy.orm import Query
from typing import List, Dict, Any

class Paginator:
    def __init__(self, query: Query, page: int = 1, per_page: int = 20):
        self.query = query
        self.page = page
        self.per_page = per_page
        self.total = query.count()
        
    def get_items(self) -> List[Any]:
        """Retorna itens da página atual"""
        offset = (self.page - 1) * self.per_page
        return self.query.offset(offset).limit(self.per_page).all()
    
    def get_pagination_info(self) -> Dict:
        """Retorna informações de paginação"""
        total_pages = (self.total + self.per_page - 1) // self.per_page
        
        return {
            'page': self.page,
            'per_page': self.per_page,
            'total': self.total,
            'total_pages': total_pages,
            'has_prev': self.page > 1,
            'has_next': self.page < total_pages,
            'prev_page': self.page - 1 if self.page > 1 else None,
            'next_page': self.page + 1 if self.page < total_pages else None
        }

# Uso nos endpoints
@router.get("/clientes")
async def get_clientes(page: int = 1, per_page: int = 20):
    query = db.query(Cliente)
    paginator = Paginator(query, page, per_page)
    
    return {
        'items': paginator.get_items(),
        'pagination': paginator.get_pagination_info()
    }
```

### Fase 4: Otimização de Frontend (Prioridade Baixa)

#### 4.1 Lazy Loading para Gráficos

**Arquivo**: `templates/crm-dashboard.jinja2`

```javascript
// ✅ CARREGAMENTO ASSÍNCRONO
async function loadDashboardData() {
    try {
        // Mostrar loading
        showLoading();
        
        // Carregar dados em paralelo
        const [statsData, chartsData] = await Promise.all([
            fetch('/ajax/dashboard-stats'),
            fetch('/ajax/dashboard-charts')
        ]);
        
        const stats = await statsData.json();
        const charts = await chartsData.json();
        
        // Atualizar interface
        updateStats(stats);
        updateCharts(charts);
        
    } catch (error) {
        console.error('Erro ao carregar dashboard:', error);
    } finally {
        hideLoading();
    }
}

// Debounce para pesquisas
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Pesquisa com debounce
const searchClientes = debounce(async (term) => {
    if (term.length < 3) return;
    
    const response = await fetch(`/ajax/search-clientes?q=${term}`);
    const results = await response.json();
    updateSearchResults(results);
}, 300);
```

#### 4.2 Compressão de Assets

**Arquivo**: `app/main.py`

```python
# ✅ COMPRESSÃO E CACHE
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles

# Adicionar compressão
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Cache para arquivos estáticos
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

# Headers de cache
@app.middleware("http")
async def add_cache_headers(request: Request, call_next):
    response = await call_next(request)
    
    # Cache para assets estáticos
    if request.url.path.startswith("/static"):
        response.headers["Cache-Control"] = "public, max-age=31536000"
    
    return response
```

## 📊 Monitoramento de Performance

### Métricas Importantes

```python
# ✅ MIDDLEWARE DE MONITORAMENTO
import time
from fastapi import Request

@app.middleware("http")
async def add_performance_monitoring(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    
    # Log de performance
    if process_time > 1.0:  # Requests lentos
        logger.warning(f"Slow request: {request.url} - {process_time:.2f}s")
    
    response.headers["X-Process-Time"] = str(process_time)
    
    return response
```

### Ferramentas de Monitoramento

```python
# requirements.txt
# Adicionar para monitoramento
prometheus-client==0.18.0
psutil==5.9.0

# app/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Métricas customizadas
REQUEST_COUNT = Counter('requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('request_duration_seconds', 'Request duration')
DATABASE_CONNECTIONS = Gauge('database_connections_active', 'Active DB connections')
```

## 🚀 Resultados Esperados

### Melhorias de Performance

**Database Queries:**
- Redução de 80% no tempo de resposta das listagens
- Diminuição de 90% no número de queries

**Cache Implementation:**
- Redução de 70% no tempo de resposta para dados estáticos
- Diminuição de 60% na carga do banco de dados

**Paginação:**
- Melhoria de 85% no tempo de carregamento de listas grandes
- Redução de 95% no uso de memória

### Cronograma de Implementação

**Semana 1**: Otimização de queries e índices
**Semana 2**: Implementação de cache Redis
**Semana 3**: Sistema de paginação
**Semana 4**: Otimizações de frontend e monitoramento

## 📋 Checklist de Implementação

### Database Optimization
- [ ] Criar índices de performance
- [ ] Implementar eager loading
- [ ] Otimizar queries N+1
- [ ] Criar repositórios especializados

### Cache Implementation
- [ ] Configurar Redis
- [ ] Implementar cache decorators
- [ ] Cache para dados estáticos
- [ ] Estratégias de invalidação

### Paginação
- [ ] Sistema de paginação universal
- [ ] Paginação nos endpoints
- [ ] Paginação no frontend
- [ ] Otimização de contagem

### Monitoramento
- [ ] Métricas de performance
- [ ] Logging estruturado
- [ ] Alertas de performance
- [ ] Dashboard de monitoramento

Com essas otimizações, o CrmSalao terá performance significativamente melhorada e estará preparado para escalar conforme o crescimento dos usuários.