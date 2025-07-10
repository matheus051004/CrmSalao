# Recomendações de Segurança - CrmSalao

## 🔒 Questões de Segurança Identificadas

### 1. **CRÍTICO**: Credenciais Expostas no Dockerfile

**Problema**: Senhas e chaves de API estão expostas em texto plano no Dockerfile.

**Arquivo**: `Dockerfile` (linhas 15-33)

```dockerfile
# ❌ VULNERABILIDADE CRÍTICA
ENV CRM_PASSWORD="admin321"
ENV API_KEY="e3121c21-dfd5-42c3-bc74-5e71dad28c91"
ENV POSTGRES_PASSWORD="e3121c21-dfd5-42c3-bc74-5e71dad28c91"
ENV WAHA_API_KEY="e3121c21-dfd5-42c3-bc74-5e71dad28c91"
```

**Riscos**:
- Exposição de credenciais em repositório público
- Acesso não autorizado ao banco de dados
- Comprometimento da API WhatsApp
- Acesso administrativo ao sistema

**Solução Imediata**:
```dockerfile
# ✅ SOLUÇÃO SEGURA
ENV CRM_PASSWORD="${CRM_PASSWORD}"
ENV API_KEY="${API_KEY}"
ENV POSTGRES_PASSWORD="${POSTGRES_PASSWORD}"
ENV WAHA_API_KEY="${WAHA_API_KEY}"
```

### 2. **ALTO**: Autenticação Simples

**Problema**: Autenticação baseada apenas em cookies simples.

**Arquivo**: `app/middlewares/AuthMiddleware.py`

```python
# ❌ AUTENTICAÇÃO FRACA
username = request.cookies.get("username")
password = request.cookies.get("password")
```

**Riscos**:
- Senhas armazenadas em texto plano nos cookies
- Fácil interceptação de credenciais
- Não há expiração de sessão
- Vulnerável a ataques de força bruta

**Solução Recomendada**:
```python
# ✅ AUTENTICAÇÃO SEGURA
# Implementar JWT tokens
# Hash das senhas
# Expiração de sessão
# Rate limiting
```

### 3. **MÉDIO**: Falta de Validação de Entrada

**Problema**: Algumas entradas não são validadas adequadamente.

**Arquivo**: `app/routers/n8n_api/agendamentos.py`

```python
# ❌ VALIDAÇÃO INSUFICIENTE
servicos_ids = [int(idd.strip()) for idd in servicos_ids.split(",")]
```

**Riscos**:
- Injeção de código
- Dados corrompidos
- Falhas de aplicação

### 4. **MÉDIO**: Tratamento de Erro Expondo Informações

**Problema**: Erros podem expor informações sensíveis.

```python
# ❌ EXPOSIÇÃO DE ERROS
return response(False, f"Erro ao criar agendamento: {str(e)}")
```

**Riscos**:
- Exposição de estrutura do banco
- Informações sobre o sistema
- Facilita ataques direcionados

## 🛡️ Plano de Correção de Segurança

### Fase 1: Correções Críticas (Imediato)

1. **Remover credenciais do Dockerfile**
   ```bash
   # Criar arquivo .env para desenvolvimento
   echo "CRM_PASSWORD=admin321" > .env.example
   echo "API_KEY=sua-chave-aqui" >> .env.example
   
   # Atualizar .gitignore
   echo ".env" >> .gitignore
   ```

2. **Implementar variáveis de ambiente**
   ```python
   # app/config.py
   import os
   from dotenv import load_dotenv
   
   load_dotenv()
   
   class Settings:
       CRM_PASSWORD = os.getenv("CRM_PASSWORD")
       API_KEY = os.getenv("API_KEY")
       POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
   ```

### Fase 2: Melhorias de Autenticação (Curto Prazo)

1. **Implementar JWT**
   ```python
   # app/auth/jwt_handler.py
   import jwt
   from datetime import datetime, timedelta
   
   def create_access_token(data: dict):
       to_encode = data.copy()
       expire = datetime.utcnow() + timedelta(minutes=15)
       to_encode.update({"exp": expire})
       return jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
   ```

2. **Hash de senhas**
   ```python
   # app/auth/password.py
   from passlib.context import CryptContext
   
   pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
   
   def hash_password(password: str) -> str:
       return pwd_context.hash(password)
   ```

### Fase 3: Validação e Sanitização (Médio Prazo)

1. **Validação rigorosa de entrada**
   ```python
   # app/models/validators.py
   from pydantic import BaseModel, validator
   
   class AgendamentoCreate(BaseModel):
       servicos_ids: List[int]
       
       @validator('servicos_ids')
       def validate_servicos_ids(cls, v):
           if not v or len(v) == 0:
               raise ValueError('Pelo menos um serviço deve ser selecionado')
           return v
   ```

2. **Rate limiting**
   ```python
   # app/middlewares/rate_limit.py
   from slowapi import Limiter
   from slowapi.util import get_remote_address
   
   limiter = Limiter(key_func=get_remote_address)
   
   @limiter.limit("5/minute")
   async def login():
       # Implementação
   ```

### Fase 4: Monitoramento e Logs (Longo Prazo)

1. **Logging estruturado**
   ```python
   # app/logging_config.py
   import logging
   import json
   from datetime import datetime
   
   def setup_logging():
       logging.basicConfig(
           level=logging.INFO,
           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
       )
   ```

2. **Auditoria de segurança**
   ```python
   # app/models/audit_log.py
   class AuditLog(Base):
       __tablename__ = 'audit_logs'
       
       id = Column(Integer, primary_key=True)
       user_id = Column(Integer, nullable=True)
       action = Column(String, nullable=False)
       resource = Column(String, nullable=False)
       timestamp = Column(DateTime, default=datetime.utcnow)
       ip_address = Column(String)
   ```

## 🔍 Checklist de Segurança

### Implementação Imediata
- [ ] Remover credenciais do Dockerfile
- [ ] Criar sistema de variáveis de ambiente
- [ ] Implementar .env.example
- [ ] Atualizar .gitignore

### Melhorias de Autenticação
- [ ] Implementar JWT tokens
- [ ] Hash de senhas com bcrypt
- [ ] Expiração de sessão
- [ ] Rate limiting para login

### Validação e Sanitização
- [ ] Validação rigorosa de entrada
- [ ] Sanitização de dados
- [ ] Tratamento de erros sem exposição
- [ ] Validação de tipos de arquivo

### Monitoramento
- [ ] Logging estruturado
- [ ] Auditoria de ações
- [ ] Monitoramento de tentativas de login
- [ ] Alertas de segurança

## 📋 Ferramentas Recomendadas

### Dependências de Segurança
```txt
# Adicionar ao requirements.txt
passlib[bcrypt]==1.7.4
python-jose[cryptography]==3.3.0
python-multipart==0.0.6
slowapi==0.1.9
python-dotenv==1.0.0
```

### Ferramentas de Análise
- **Bandit**: Análise de vulnerabilidades
- **Safety**: Verificação de dependências
- **Semgrep**: Análise estática de código

### Comandos para Verificação
```bash
# Instalar ferramentas
pip install bandit safety

# Verificar vulnerabilidades
bandit -r app/
safety check

# Verificar secrets
git secrets --scan
```

## 🚨 Ações Prioritárias

1. **URGENTE**: Remover credenciais do Dockerfile
2. **ALTA**: Implementar autenticação JWT
3. **MÉDIA**: Adicionar validação de entrada
4. **BAIXA**: Implementar auditoria completa

## 📞 Suporte

Para implementar essas correções, recomendo:

1. **Backup completo** do sistema atual
2. **Ambiente de teste** para validar mudanças
3. **Implementação gradual** das correções
4. **Testes de segurança** após cada fase

Esta análise identifica as principais vulnerabilidades e fornece um roteiro claro para melhorar a segurança do sistema CrmSalao.