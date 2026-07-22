from typing import Any
from fastapi import FastAPI, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.config import get_settings
from app.services.bandwidth import BandwidthAPIError, BandwidthClient
settings=get_settings(); app=FastAPI(title=settings.app_name); app.mount("/static",StaticFiles(directory="app/static"),name="static"); templates=Jinja2Templates(directory="app/templates"); bw=BandwidthClient(settings)
def render(request,template,**ctx):
    b={"request":request,"app_name":settings.app_name,"account_id":settings.bandwidth_account_id}; b.update(ctx); return templates.TemplateResponse(template,b)
@app.get("/",response_class=HTMLResponse)
async def dashboard(request:Request):
    try:d=await bw.list_sites(); sites=d.get("subAccounts",[]); err=None
    except BandwidthAPIError as e: sites=[]; err=str(e)
    return render(request,"dashboard.html",sites=sites,total_numbers=sum(int(x.get("totalPhoneNumberCount",0) or 0) for x in sites),total_locations=sum(int(x.get("locationCount",0) or 0) for x in sites),error=err)
@app.get("/sites",response_class=HTMLResponse)
async def sites(request:Request):
    try:return render(request,"sites.html",sites=(await bw.list_sites()).get("subAccounts",[]),error=None)
    except BandwidthAPIError as e:return render(request,"sites.html",sites=[],error=str(e))
@app.get("/sites/{site_id}/locations/{location_id}/numbers",response_class=HTMLResponse)
async def nums(request:Request,site_id:int,location_id:int,site_name:str="",location_name:str="",page:str|None=Query(None),size:int=50):
    try:d=await bw.list_location_numbers(site_id,location_id,page,size); return render(request,"numbers.html",site_name=site_name,location_name=location_name,phone_numbers=d.get("phoneNumbers",[]),error=None)
    except BandwidthAPIError as e:return render(request,"numbers.html",site_name=site_name,location_name=location_name,phone_numbers=[],error=str(e))
@app.get("/available-numbers",response_class=HTMLResponse)
async def available(request:Request,areaCode:str="",quantity:str="",state:str="",city:str="",rateCenter:str=""):
    vals=locals().copy(); searched=any([areaCode,quantity,state,city,rateCenter]); results=[]; err=None
    if searched:
        try:results=(await bw.search_available_numbers({"areaCode":areaCode,"quantity":quantity,"state":state,"city":city,"rateCenter":rateCenter})).get("metadata",[])
        except BandwidthAPIError as e:err=str(e)
    return render(request,"available.html",values=vals,searched=searched,results=results,error=err)
@app.get("/csrs",response_class=HTMLResponse)
async def csrs(request:Request):
    try:return render(request,"csrs.html",csr_orders=(await bw.list_csrs()).get("csrOrders",[]),error=None)
    except BandwidthAPIError as e:return render(request,"csrs.html",csr_orders=[],error=str(e))
@app.get("/csrs/new",response_class=HTMLResponse)
async def csr_new(request:Request):return render(request,"csr_new.html",error=None)
@app.post("/csrs/new")
async def csr_create(request:Request,workingOrBillingTelephoneNumber:str=Form(...),accountNumber:str=Form(""),accountTelephoneNumber:str=Form(""),endUserName:str=Form(""),authorizingUserName:str=Form(""),customerCode:str=Form(""),endUserPin:str=Form(""),endUserPassword:str=Form(""),addressLine1:str=Form(""),city:str=Form(""),state:str=Form(""),zipCode:str=Form(""),typeOfService:str=Form("residential")):
    p={k:v for k,v in locals().items() if k not in {"request"} and v!=""}
    try:await bw.create_csr(p); return RedirectResponse("/csrs",303)
    except BandwidthAPIError as e:return render(request,"csr_new.html",error=str(e))
@app.get("/ports",response_class=HTMLResponse)
async def ports(request:Request,site_id:int|None=None):
    try:
        sites=(await bw.list_sites()).get("subAccounts",[]); site_id=site_id or (int(sites[0]["id"]) if sites else None); ps=(await bw.list_portins(site_id)).get("portins",[]) if site_id else []; err=None
    except BandwidthAPIError as e:sites=[];ps=[];err=str(e)
    return render(request,"ports.html",sites=sites,selected_site_id=site_id,portins=ps,error=err)
@app.get("/ports/new",response_class=HTMLResponse)
async def port_new(request:Request):
    try:return render(request,"port_new.html",sites=(await bw.list_sites()).get("subAccounts",[]),error=None)
    except BandwidthAPIError as e:return render(request,"port_new.html",sites=[],error=str(e))
@app.post("/ports/new")
async def port_create(request:Request,customerOrderId:str=Form(...),loaAuthorizingPerson:str=Form(...),subAccountId:int=Form(...),locationId:int=Form(...),phoneNumbers:str=Form(...),requestedFocDate:str=Form(""),targetRespOrgId:str=Form("")):
    p={"customerOrderId":customerOrderId,"loaAuthorizingPerson":loaAuthorizingPerson,"subAccountId":subAccountId,"locationId":locationId,"phoneNumbers":[x.strip() for x in phoneNumbers.replace(",","\n").splitlines() if x.strip()]};
    if requestedFocDate:p["requestedFocDate"]=requestedFocDate
    if targetRespOrgId:p["targetRespOrgId"]=targetRespOrgId
    try:r=await bw.create_portin(p); return RedirectResponse(f"/ports/{r.get('orderId')}" if r.get('orderId') else f"/ports?site_id={subAccountId}",303)
    except BandwidthAPIError as e:return render(request,"port_new.html",sites=(await bw.list_sites()).get("subAccounts",[]),error=str(e))
@app.get("/ports/{order_id}",response_class=HTMLResponse)
async def port_detail(request:Request,order_id:str):
    try:return render(request,"port_detail.html",order=await bw.get_portin(order_id),order_id=order_id,error=None)
    except BandwidthAPIError as e:return render(request,"port_detail.html",order={},order_id=order_id,error=str(e))
@app.post("/ports/{order_id}/cancel")
async def cancel(request:Request,order_id:str):
    await bw.cancel_portin(order_id); return RedirectResponse(f"/ports/{order_id}",303)
