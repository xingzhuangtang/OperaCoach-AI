"""
衬字谱 API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from app.processors.chenzi import ChenziMapper

router = APIRouter()
mapper = ChenziMapper()


class NotationConvertRequest(BaseModel):
    notation: str
    separator: Optional[str] = "-"


class NotationBatchConvertRequest(BaseModel):
    notations: List[str]
    separator: Optional[str] = "-"


@router.post("/convert")
async def convert_notation(request: NotationConvertRequest):
    """
    快速转换单个数字简谱为衬字谱
    POST /api/v1/chenzi/convert {"notation": "3 5 6 1 2"}
    返回: {"chenzi": "咦-呜-呀-啊-哎", "parsed": [...]}
    """
    try:
        chenzi_string = mapper.to_chenzi_string(request.notation, request.separator)
        parsed = mapper.parse_notation(request.notation)
        return {
            "notation": request.notation,
            "chenzi": chenzi_string,
            "parsed": parsed,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/batch-convert")
async def batch_convert_notation(request: NotationBatchConvertRequest):
    """
    批量转换数字简谱为衬字谱
    POST /api/v1/chenzi/batch-convert {"notations": ["3 5 6 1 2", "1 2 3"]}
    返回: [{"notation": "...", "chenzi": "..."}, ...]
    """
    try:
        results = []
        for notation in request.notations:
            chenzi_string = mapper.to_chenzi_string(notation, request.separator)
            results.append({
                "notation": notation,
                "chenzi": chenzi_string,
            })
        return {"results": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/mapping")
async def get_mapping():
    """获取衬字映射表"""
    return {
        "mapping": mapper.get_mapping_table(),
        "description": "数字简谱到衬字语气词的映射规则",
    }
