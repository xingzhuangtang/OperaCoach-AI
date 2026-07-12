"""
API 路由
"""
from fastapi import APIRouter

from app.api.v1 import auth, upload, segments, chenzi, music

router = APIRouter()

# v1 路由
router.include_router(auth.router, prefix="/auth", tags=["认证"])
router.include_router(upload.router, prefix="/upload", tags=["上传"])
router.include_router(segments.router, prefix="/segments", tags=["唱段"])
router.include_router(chenzi.router, prefix="/chenzi", tags=["衬字谱"])
router.include_router(music.router, prefix="/music", tags=["AI 作曲"])
