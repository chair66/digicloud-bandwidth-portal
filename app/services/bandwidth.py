from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Any
import httpx
from app.config import Settings

class BandwidthAPIError(RuntimeError):
    def __init__(self, message: str, status_code: int|None=None, payload: Any=None):
        super().__init__(message); self.status_code=status_code; self.payload=payload

class BandwidthClient:
    def __init__(self, settings: Settings):
        self.settings=settings; self._access_token=None; self._token_expires_at=None
    async def _get_access_token(self)->str:
        now=datetime.now(timezone.utc)
        if self._access_token and self._token_expires_at and now < self._token_expires_at: return self._access_token
        async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
            r=await client.post(self.settings.bandwidth_token_url,data={"grant_type":"client_credentials"},auth=(self.settings.bandwidth_client_id,self.settings.bandwidth_client_secret),headers={"Accept":"application/json"})
        if r.is_error: raise BandwidthAPIError(f"OAuth token request failed with HTTP {r.status_code}.",r.status_code,_safe(r))
        p=r.json(); token=p.get("access_token")
        if not token: raise BandwidthAPIError("OAuth response did not include access_token.",payload=p)
        self._access_token=token; self._token_expires_at=now+timedelta(seconds=max(int(p.get("expires_in",3600))-60,60)); return token
    async def request(self,method:str,path:str,params=None,json_body=None):
        token=await self._get_access_token(); url=path if path.startswith("http") else f"{self.settings.bandwidth_api_base.rstrip('/')}/{path.lstrip('/')}"
        async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
            r=await client.request(method,url,params=params,json=json_body,headers={"Authorization":f"Bearer {token}","Accept":"application/json","Content-Type":"application/json"})
        if r.is_error:
            p=_safe(r); raise BandwidthAPIError(_message(p) or f"Bandwidth returned HTTP {r.status_code}.",r.status_code,p)
        return {} if r.status_code==204 or not r.content else r.json()
    @property
    def account_id(self): return self.settings.bandwidth_account_id
    async def list_sites(self): return await self.request("GET",f"/accounts/{self.account_id}/sites")
    async def list_location_numbers(self,site_id,location_id,page=None,size=50):
        q={"size":size}; q.update({"page":page} if page else {}); return await self.request("GET",f"/accounts/{self.account_id}/sites/{site_id}/sippeers/{location_id}/tns",params=q)
    async def search_available_numbers(self,q): return await self.request("GET",f"/accounts/{self.account_id}/availableNumbers",params={k:v for k,v in q.items() if v not in (None,"")})
    async def list_csrs(self): return await self.request("GET",f"/accounts/{self.account_id}/csrs")
    async def create_csr(self,p): return await self.request("POST",f"/accounts/{self.account_id}/csrs",json_body=p)
    async def list_portins(self,site_id): return await self.request("GET",f"/accounts/{self.account_id}/sites/{site_id}/portins")
    async def get_portin(self,order_id): return await self.request("GET",f"/accounts/{self.account_id}/portins/{order_id}")
    async def create_portin(self,p): return await self.request("POST",f"/accounts/{self.account_id}/portins",json_body=p)
    async def cancel_portin(self,order_id): return await self.request("DELETE",f"/accounts/{self.account_id}/portins/{order_id}")

def _safe(r):
    try:return r.json()
    except:return r.text
def _message(p):
    if isinstance(p,dict):
        e=p.get("errors")
        if isinstance(e,list) and e and isinstance(e[0],dict): return e[0].get("description") or e[0].get("message")
        s=p.get("status")
        if isinstance(s,dict): return s.get("description")
        return p.get("message") or p.get("description")
