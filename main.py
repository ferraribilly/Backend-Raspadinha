from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
import os
import logging
import uuid
import random
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Raspadinha Premiada API",
    description="API para jogo de raspadinha com integração Mercado Pago",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar domínios
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Models
class TicketPurchase(BaseModel):
    ticket_price: float
    payment_method: str
    player_id: Optional[str] = None

class PaymentRequest(BaseModel):
    amount: float
    payment_method: str
    payment_data: Dict[str, Any]

class PaymentResponse(BaseModel):
    success: bool
    payment_id: str
    status: str
    message: str
    ticket_id: Optional[str] = None

# Simulador de sistema de prêmios
class PrizeSystem:
    def __init__(self):
        self.prize_pools = {
            5: [
                {"amount": 0, "probability": 0.75, "message": "Tente novamente!"},
                {"amount": 5, "probability": 0.15, "message": "Recuperou o valor!"},
                {"amount": 15, "probability": 0.08, "message": "Triplicou!"},
                {"amount": 50, "probability": 0.019, "message": "Grande prêmio!"},
                {"amount": 250, "probability": 0.001, "message": "JACKPOT!"}
            ],
            10: [
                {"amount": 0, "probability": 0.70, "message": "Tente novamente!"},
                {"amount": 10, "probability": 0.18, "message": "Recuperou o valor!"},
                {"amount": 30, "probability": 0.10, "message": "Triplicou!"},
                {"amount": 100, "probability": 0.019, "message": "Grande prêmio!"},
                {"amount": 500, "probability": 0.001, "message": "JACKPOT!"}
            ],
            25: [
                {"amount": 0, "probability": 0.65, "message": "Tente novamente!"},
                {"amount": 25, "probability": 0.20, "message": "Recuperou o valor!"},
                {"amount": 75, "probability": 0.12, "message": "Triplicou!"},
                {"amount": 250, "probability": 0.029, "message": "Grande prêmio!"},
                {"amount": 1000, "probability": 0.001, "message": "JACKPOT!"}
            ],
            50: [
                {"amount": 0, "probability": 0.60, "message": "Tente novamente!"},
                {"amount": 50, "probability": 0.22, "message": "Recuperou o valor!"},
                {"amount": 150, "probability": 0.15, "message": "Triplicou!"},
                {"amount": 500, "probability": 0.029, "message": "Grande prêmio!"},
                {"amount": 2500, "probability": 0.001, "message": "JACKPOT!"}
            ]
        }
    
    def generate_prize(self, ticket_price: float) -> Dict[str, Any]:
        """Gera um prêmio baseado no preço do bilhete e probabilidades"""
        prizes = self.prize_pools.get(ticket_price, self.prize_pools[5])
        
        # Gerar número aleatório
        random_value = random.random()
        cumulative_probability = 0.0
        
        # Selecionar prêmio baseado na probabilidade
        for prize in prizes:
            cumulative_probability += prize["probability"]
            if random_value <= cumulative_probability:
                return {
                    "amount": prize["amount"],
                    "message": prize["message"],
                    "is_winner": prize["amount"] > 0,
                    "prize_tier": self._get_prize_tier(prize["amount"]),
                    "timestamp": datetime.now().isoformat()
                }
        
        # Fallback (não deveria acontecer com probabilidades corretas)
        return {
            "amount": 0,
            "message": "Tente novamente!",
            "is_winner": False,
            "prize_tier": "none",
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_prize_tier(self, amount: float) -> str:
        """Determina o tier do prêmio baseado no valor"""
        if amount >= 1000:
            return "jackpot"
        elif amount >= 100:
            return "major"
        elif amount >= 10:
            return "minor"
        elif amount > 0:
            return "consolation"
        else:
            return "none"

# Simulador do Mercado Pago
class MercadoPagoSimulator:
    def __init__(self):
        self.transactions = {}
    
    def process_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simula processamento de pagamento no Mercado Pago"""
        payment_id = f"mp_payment_{uuid.uuid4().hex[:10]}"
        
        # Simular diferentes cenários de pagamento
        success_rate = 0.85  # 85% de sucesso
        
        if random.random() < success_rate:
            status = "approved"
            status_detail = "accredited"
            message = "Pagamento aprovado com sucesso"
        else:
            # Simular falhas comuns
            failure_scenarios = [
                {"status": "rejected", "detail": "cc_rejected_insufficient_amount", "message": "Saldo insuficiente"},
                {"status": "rejected", "detail": "cc_rejected_bad_filled_security_code", "message": "Código de segurança inválido"},
                {"status": "pending", "detail": "pending_waiting_payment", "message": "Aguardando pagamento"},
                {"status": "rejected", "detail": "cc_rejected_call_for_authorize", "message": "Pagamento não autorizado"}
            ]
            
            scenario = random.choice(failure_scenarios)
            status = scenario["status"]
            status_detail = scenario["detail"]
            message = scenario["message"]
        
        # Armazenar transação
        transaction = {
            "id": payment_id,
            "status": status,
            "status_detail": status_detail,
            "transaction_amount": payment_data.get("amount", 0),
            "payment_method_id": payment_data.get("payment_method", "unknown"),
            "date_created": datetime.now().isoformat(),
            "date_approved": datetime.now().isoformat() if status == "approved" else None,
            "payer": payment_data.get("payer", {}),
            "metadata": payment_data.get("metadata", {})
        }
        
        self.transactions[payment_id] = transaction
        
        return {
            "id": payment_id,
            "status": status,
            "status_detail": status_detail,
            "message": message,
            "transaction_amount": payment_data.get("amount", 0)
        }
    
    def get_payment(self, payment_id: str) -> Optional[Dict[str, Any]]:
        """Recupera informações de um pagamento"""
        return self.transactions.get(payment_id)

# Instanciar sistemas
prize_system = PrizeSystem()
mp_simulator = MercadoPagoSimulator()

# Armazenamento em memória (em produção, usar banco de dados)
tickets_db = {}
payments_db = {}

@app.get("/")
async def root():
    return {"message": "Raspadinha Premiada API está funcionando!"}

@app.get("/api/")
async def api_root():
    return {
        "message": "API da Raspadinha Premiada",
        "version": "1.0.0",
        "status": "online"
    }

@app.post("/api/process-payment")
async def process_payment(payment_request: PaymentRequest):
    """Processa pagamento e gera bilhete"""
    try:
        logger.info(f"Processando pagamento: R$ {payment_request.amount}")
        
        # Validar preço do bilhete
        valid_prices = [5, 10, 25, 50]
        if payment_request.amount not in valid_prices:
            raise HTTPException(status_code=400, detail="Preço de bilhete inválido")
        
        # Simular processamento no Mercado Pago
        mp_payment_data = {
            "amount": payment_request.amount,
            "payment_method": payment_request.payment_method,
            "payer": {"email": "test@example.com"},
            "metadata": {"game_type": "scratch_lottery"}
        }
        
        mp_result = mp_simulator.process_payment(mp_payment_data)
        
        # Salvar pagamento
        payments_db[mp_result["id"]] = {
            "payment_id": mp_result["id"],
            "amount": payment_request.amount,
            "status": mp_result["status"],
            "created_at": datetime.now().isoformat()
        }
        
        if mp_result["status"] == "approved":
            # Gerar bilhete e prêmio
            ticket_id = f"ticket_{uuid.uuid4().hex[:8]}"
            prize = prize_system.generate_prize(payment_request.amount)
            
            ticket = {
                "id": ticket_id,
                "payment_id": mp_result["id"],
                "price": payment_request.amount,
                "prize": prize,
                "created_at": datetime.now().isoformat(),
                "scratched": False
            }
            
            tickets_db[ticket_id] = ticket
            
            logger.info(f"Bilhete gerado: {ticket_id} - Prêmio: R$ {prize['amount']}")
            
            return PaymentResponse(
                success=True,
                payment_id=mp_result["id"],
                status="approved",
                message="Pagamento aprovado! Bilhete gerado com sucesso.",
                ticket_id=ticket_id
            )
        else:
            # Pagamento não aprovado
            return PaymentResponse(
                success=False,
                payment_id=mp_result["id"],
                status=mp_result["status"],
                message=mp_result["message"],
                ticket_id=None
            )
    
    except Exception as e:
        logger.error(f"Erro no processamento: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.get("/api/ticket/{ticket_id}")
async def get_ticket(ticket_id: str):
    """Recupera informações de um bilhete"""
    ticket = tickets_db.get(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Bilhete não encontrado")
    
    return ticket

@app.post("/api/scratch-ticket/{ticket_id}")
async def scratch_ticket(ticket_id: str):
    """Marca bilhete como raspado e revela prêmio"""
    ticket = tickets_db.get(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Bilhete não encontrado")
    
    if ticket["scratched"]:
        raise HTTPException(status_code=400, detail="Bilhete já foi raspado")
    
    # Marcar como raspado
    tickets_db[ticket_id]["scratched"] = True
    tickets_db[ticket_id]["scratched_at"] = datetime.now().isoformat()
    
    logger.info(f"Bilhete raspado: {ticket_id} - Prêmio: R$ {ticket['prize']['amount']}")
    
    return {
        "ticket_id": ticket_id,
        "prize": ticket["prize"],
        "message": "Bilhete raspado com sucesso!"
    }

@app.get("/api/statistics")
async def get_statistics():
    """Retorna estatísticas do jogo"""
    total_tickets = len(tickets_db)
    total_payments = sum(t["price"] for t in tickets_db.values())
    total_prizes = sum(t["prize"]["amount"] for t in tickets_db.values() if t["scratched"])
    winners = [t for t in tickets_db.values() if t["scratched"] and t["prize"]["amount"] > 0]
    
    return {
        "total_tickets": total_tickets,
        "total_payments": total_payments,
        "total_prizes": total_prizes,
        "winners_count": len(winners),
        "win_rate": len(winners) / total_tickets if total_tickets > 0 else 0,
        "house_edge": (total_payments - total_prizes) / total_payments if total_payments > 0 else 0
    }

@app.get("/api/health")
async def health_check():
    """Endpoint de health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "tickets_count": len(tickets_db),
        "payments_count": len(payments_db)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)