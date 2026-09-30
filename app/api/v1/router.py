from fastapi import APIRouter
from app.api.v1 import auth, profile, chat, policies, compare, claims, premium, recommendations, faqs, documents

api_v1_router = APIRouter()

api_v1_router.include_router(auth.router)
api_v1_router.include_router(profile.router)
api_v1_router.include_router(chat.router)
api_v1_router.include_router(policies.router)
api_v1_router.include_router(compare.router)
api_v1_router.include_router(claims.router)
api_v1_router.include_router(premium.router)
api_v1_router.include_router(recommendations.router)
api_v1_router.include_router(faqs.router)
api_v1_router.include_router(documents.router)
