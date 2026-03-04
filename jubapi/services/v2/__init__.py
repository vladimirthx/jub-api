from jubapi.repositories.v2 import ObservatoriesRepository,XVariablesRepository,ProductRepository,XVariableAssignmentRepository,XVariableParentRelationshipRepository
from jubapi.models.v2 import XVariableModel,ObservatoryModel,ProductModel,XVariableAssignment,ContentVars,PlotDescription,ContextualVars,XVariableType,XType,XVariableParentRelationshipModel
from jubapi.dto.v2 import ObservatoryDTO,XVariableDTO,ProductDTO,MultipleXVariableAssignmentDTO,ManyProductsMultipleXVariableAssignmentDTO,XVariableRawAssignmentDTO,SVResult,TVResult,IVResult,PTResult,XVariableInfoDTO,TemporalVariableInfo,ProductFoundDTO,XVariableMultipleInfoWithXVId,XVariableParentRelationshipDTO
from option import Result,Ok,Err
from nanoid import generate as nanoid
from jubapi.errors import JubError,UnknownError,NotFound,AlreadyExists
from typing import List,Tuple,Dict,Any,Coroutine
import hashlib as H
import asyncio
import json as J
# from hashlib import _Hash
from jubapi.querylang.peg import parse,parse_sv,parse_pt,parse_iv,parse_tv
from jubapi.querylang.dto import ProductCreationDTO

class OcaNameService:
    def __init__(self, 
        xvariable_assignments_repo:XVariableAssignmentRepository,
        product_repo: ProductRepository
    ):
        self.xvariable_assignments_repo = xvariable_assignments_repo
        self.product_repo = product_repo

    async def filter(self, query:str,strict:bool = False):
        try: 
            # print("QUERY",query)
            res = parse(query).asDict()
            sv  = res.get("sv")
            sv  = SVResult(**sv) if sv else None
            tv  = res.get("tv") 
            # print("TV",tv)
            tv  = TVResult(**tv) if tv else None
            iv  = res.get("iv")
            iv  = IVResult(**iv) if iv else None
            ov  = res.get("ov")
            
            pt  = res.get("pt")
            pt  = PTResult(**pt) if pt else None
            xxs = list(sv.calculate_hashes())
            ys  = list(tv.calculate_hashes())
            ws  = list(iv.calculate_hashes())

            sv_found_products:List[str] = []
            for x in xxs:
                _query = {"xvid":x.xvid}
                result = await self.xvariable_assignments_repo.find(query=_query)
                if result.is_err:
                    continue
                results = result.unwrap()
                for y in results:
                    if not y.xid in sv_found_products:
                        sv_found_products.append(y.xid)

            tv_found_products:List[str] = []
            for y in ys:
                for xvid in y.xvid:
                    _query = {"xvid":xvid}
                    result = await self.xvariable_assignments_repo.find(query=_query)
                    if result.is_err:
                        continue
                    results = result.unwrap()
                    for r in results:
                        if not r.xid in tv_found_products:
                            tv_found_products.append(r.xid)
            
            for w in ws:
                print("W",w)
            print("SV_FP", sv_found_products)
            print("TV_FP",tv_found_products)

            
                # print("Y",y)

            # for (i, p) in found_products:
            # async def run_and_keep(cr: Coroutine[Any, Any, Result[ProductDTO, Exception]], x):
            #     result = await cr
            #     return result,x
            # products = [ run_and_keep(self.product_repo.find_by_pid(pid= i), xvm) for (i,xvm) in found_products]
            # products:List[Tuple[Result[ProductDTO,Exception],XVariableMultipleInfoWithXVId]] = await asyncio.gather(*products)
            # products = list(map(lambda x: (x[0].unwrap(),x[1]),filter(lambda x: x[0].is_ok, products)))
            # pfs = []
            # for (p,xvm) in products:
            #     pf = ProductFoundDTO(
            #         pid = p.pid,
            #         description=p.description,
            #         name= p.name,
            #         tags= list(xvm.to_tags()),
            #     )
            #     pfs.append(pf)
            pfs = []
            return pfs
        except Exception as e:
            print("ERROR",e)
            # return Err(e)
            # print("RESULTS",results)
                
            #     resp = result.unwrap()
            #     if not resp.xid in found_products:
            #         # print("PRODUCT",product)
            #         temp_xid = resp.xid
            #         # found_products.append(resp.xid)
            #         matches+=1
            #     else:
            #         matches+=1
            # print("MATCHES", matches)
            # if matches == len(xs):
            #     print("_"*20)
            #     print("MATCHES", temp_xid)
            #     print("xs",xs)
            #     print("_"*20)
            #     found_products.append(temp_xid)
            # temp_xid= ""
            # matches=0
            
                    # print()
                    
            
            # print(resp.xid)
            # print("RESULT", result)

        # print("XS",xs)
        # ys = list(tv.calculate_hashes())
        # print("YS",ys)
        # ws = list(iv.calculate_hashes())
        # print("WS",ws)
        # zs  = list(pt.calculate_hashes())
        # print("ZS",zs)


class XVariableParentRelationshipService:
    def __init__(self,repo:XVariableParentRelationshipRepository):
        self.repo = repo
    async def create(self, dto:XVariableParentRelationshipDTO):
        try:
            exists = await self.repo.exists(parent_id= dto.parent_id, child_id=dto.child_id)
            if exists:
                return Err(AlreadyExists("XVariable parent relationship already exists"))
            res = await self.repo.create(XVariableParentRelationshipModel(**dto.model_dump()))
            return res
        except Exception as e:
            return Err(e)
    async def create_many(self, dtos:List[XVariableParentRelationshipDTO])->Result[int, JubError]:
        try:
            async def __inner(dto):
                exists = await self.repo.exists(parent_id=dto.parent_id , child_id= dto.child_id)
                return exists, dto
            existss_coroutines = [ __inner(dto) for dto in dtos]
            existss = await asyncio.gather(*existss_coroutines)
            # print("EXISTS",existss)
            filtered_dtos = list(map(lambda x:x[1],filter(lambda x: not x[0], existss )))
            # print("FILTRED_DTOS",filtered_dtos)
            if len(filtered_dtos) ==0:
                return Ok(0)
            res = await self.repo.create_many([ XVariableParentRelationshipModel(**dto.model_dump()) for dto in filtered_dtos])
            if res.is_err:
                return res
            return len(res.unwrap())
        except Exception as e:
            return Err(e)


class ObservatoriesService:
    def __init__(self, repo: ObservatoriesRepository):
        self.repo = repo
        self.obid_aphabet = "0123456789abcdefghijklmnopqrst"
        self.obid_size = 10

    async def create(self, observatory: ObservatoryDTO) -> Result[str, JubError]:
        try:
            y = observatory.model_dump()
            print("Y",y)
            obs_model = ObservatoryModel(**y)
            if obs_model.obid == "":
                obs_model.obid = f"obs-{nanoid(alphabet=self.obid_aphabet, size=self.obid_size)}"
                
            x = await self.repo.create(obs_model)
            if x.is_err:
                return Err(UnknownError(detail="Observatory creation failed."))
            return Ok(obs_model.obid)
        except Exception as e:
            return Err(e)

    async def find_by_obid(self, obid: str) -> Result[ObservatoryModel, JubError]:
        try:
            x = self.repo.find_by_obisd(obid=obid)
        except Exception as e:
            return Err(e)

    async def update_observatory(self, obid: str, dto: ObservatoryDTO) -> bool:
        return await self.repo.update(obid, dto.model_dump())

    async def delete_observatory(self, obid: str) -> bool:
        return await self.repo.delete(obid)

class XVariablesService:
    def __init__(self,
        repo: XVariablesRepository,
        parent_relationship:XVariableParentRelationshipService,
    ):
        self.repo                = repo
        self.parent_relationship = parent_relationship

    async def create_ordered(self,xs:List[XVariableDTO])->Result[List[str],JubError]:
        try:
            ordered:List[XVariableDTO] = sorted(xs,key=lambda k: k.order)
            xvids:List[str] = []    
            parents:List[XVariableDTO] =[]
            for x in ordered:
                res = await self.create(xvariable=x)
                
                for parent in parents:
                    dto = XVariableParentRelationshipDTO(parent_id=parent.xvid, child_id=x.xvid)
                    res = await self.parent_relationship.create(dto = dto)
                parents.append(x)
            return Ok([])
        except Exception as e:
            return Err(UnknownError(detail=str(e)))
    
    def __calculate_xvid(xvar:XVariableDTO):
        hasher          = H.sha256()
        if xvar.xtype == XType.String or xvar.xtype == XType.Float or xvar.xtype == XType.Integer or xvar.xtype == XType.X:
            xbytes         = f"{xvar.type}{xvar.value}".encode("utf8")
            hasher.update(xbytes)
        elif xvar.xtype == XType.Array:
            str_xs = list(map(lambda x: str(x).upper(), xvar.value))
            xs = "".join(str_xs)
            hasher.update(xs.encode("utf-8"))
        elif xvar.xtype == XType.Date:
            date_str = xvar.value.isoformat()
            hasher.update(date_str.encode("utf-8"))
        elif xvar.xtype == XType.DateRange:
            start_date = xvar.value.start.isoformat()
            end_date   = xvar.value.end.isoformat()
            left_open  = xvar.value.left_open
            right_open = xvar.value.right_open
            left       = "(" if left_open else "["
            right      = ")" if right_open else "]"
            x = f"{left}{start_date}{end_date}{right}"
            hasher.update(x.encode("utf-8"))
        elif xvar.xtype == XType.IntegerRange or xvar.xtype == XType.Range:
            start = xvar.value.start
            end   = xvar.value.start
            step  = xvar.value.step
            x     = f"{start}{end}{step}"
            hasher.update(x.encode("utf-8"))
        elif xvar.xtype == XType.Object:
            normalized_data = J.dumps(xvar.value,sort_keys=True)
            data_bytes = normalized_data.encode("utf-8")
            hasher.update(data_bytes)
        # elif xvar.type == XType.Range:
            # pass
        # elif xvar.xtype == XType.Sequence:
            # pass
        xvid             = hasher.hexdigest()
        # xvar.xvid = xvid
        return xvid

    async def create(self, xvariable: XVariableDTO) -> Result[str, JubError]:
        try:
            hasher          = H.sha256()
            if xvariable.xvid == "":
                xvariable.xvid = self.__calculate_xvid(xvariable)

            
            exists = await self.exists(xvid=xvariable.xvid)
            if exists:
                return Err(AlreadyExists(detail="XVariable already exists."))

            
            y     = xvariable.model_dump()
            model = XVariableModel(**y)
            x     = await self.repo.create(model)
            if x.is_err:
                return x
            return Ok(model.xvid)
        except Exception as e:
            return Err(e)
    async def create_many(self, xs:List[XVariableDTO])->Result[int, JubError]:
        try:
            async def __inner(model:XVariableDTO):
                exists = await self.exists(xvid = model.xvid)
                return exists,XVariableModel(**model.model_dump())
            ys            = list(map(lambda x : __inner(x), xs ))
            # print("_"*50)
            # print("YS", ys)
            # print("_"*50)
            filtered_dtos = await asyncio.gather(*ys)
            filtered_dtos = list(map(lambda y:y[1],filter(lambda x: not x[0], filtered_dtos)))
            # print("_"*50)
            # print("FITERESL", filtered_dtos)
            # print("_"*50)
            if len(filtered_dtos) == 0:
                return Ok(0)
            res           = await self.repo.create_many(xs = filtered_dtos)
            return res
        except Exception as e:
            return Err(e)

    async def find_by_xvid(self, xvid:str)->Result[XVariableDTO, JubError]:
        try:
            x = await self.repo.find_by_xvid(xvid=xvid)
            if x.is_err:
                return Err(NotFound(detail=str(x.unwrap_err())))
            xx = x.unwrap()
            return Ok(XVariableDTO.from_model(xx))
        except Exception as e: 
            return Err(e)

    async def exists(self,xvid:str)->bool:
        try:
            res = await self.repo.exists(xvid = xvid)
            return res
        except Exception as e:
            return False

    async def find_by_type_values(self,
        type:str, 
        values:List[str]=[]
    )->Result[XVariableDTO,JubError]:
        try:
            xvids = []
            for value in values:
                x      = f"{type}{value}"
                hasher = H.sha256()
                hasher.update(x.encode("utf-8"))
                xvid   = hasher.hexdigest()
                xvids.append(xvid)
            res    = await self.repo.find_by_xvids(xvids)
            if res.is_err:
                return Err(UnknownError(detail=str(res.unwrap_err())))
            
            return Ok(res.unwrap())
        except Exception as e: 
            return Err(e)
    # async def get_variables_by_parent(self, parent_id: str) -> Result[list[XVariableModel], OcaError]:
    #     return self.repo.find_by_parent_id(parent_id)

    # async def update_variable(self, obid: str, dto: XVariableDTO) -> bool:
    #     return self.repo.update(obid, dto.dict())

    # async def delete_variable(self, obid: str) -> bool:
    #     return self.repo.delete(obid)
    
class ProductsService:
    def __init__(self, 
        repo: ProductRepository,
        xvar_repo: XVariablesRepository,
        xvar_service:XVariablesService,
        xvar_assignments_repo:XVariableAssignmentRepository,
        xvar_parent_relationship_service: XVariableParentRelationshipService
        # (repo = xvar_parent_relationship_repo)
    ):
        self.repo                            = repo
        self.xvar_assignments_repo           = xvar_assignments_repo
        self.xvar_repo                       = xvar_repo
        self.xvar_assignments_service        = XVariableAssignmentsService(repo = xvar_assignments_repo)
        self.xvar_service                    = xvar_service
        self.xvar_parent_relatioship_service = xvar_parent_relationship_service
        self.obid_aphabet                    = "0123456789abcdefghijklmnopqrst"
        self.obid_size                       = 10
    
    
    async def create(self, product:ProductCreationDTO)->Result[str, JubError]:
        try:
            parsed = product.parse()
            sv = parsed.get("sv")
            tv = parsed.get("tv")
            iv = parsed.get("iv")
            pt = parsed.get("pt")
            ov = parsed.get("ov")
            info = parsed.get("info")
            # print(parsed)
            xvar_assignments:List[XVariableAssignment] = []

            h_pid = H.sha256()
            sv_elements = sv.get("elements",[])
            sv_elements = sorted(sv_elements,key = lambda x: x["xvid"])
            pid = ""
            # print("SV_ELEMENTS",sv_elements)
            for e in sv_elements:
                _type = e.get("type")
                if not _type :
                    continue
                elif _type =="SEQUENCE":
                    items           = e.get("values")
                    items = sorted(items, key=lambda k:k["xvid"])
                    # print("ITEMS",items)
                    xvariable_models = []
                    parent_child_relationship:List[Dict[str, str]] = []
                    xvid=e.get("xvid")
                    for i,v in enumerate(items) :
                        __type  = v.get("type")
                        __value = v.get("value")
                        __xvid  = v.get("xvid")
                        xvariable_model = XVariableDTO(
                            **v,
                            variable_type=XVariableType.Spatial,
                            raw= f"{__type}({__value})"
                        )
                        xvar_assignments.append(
                            XVariableAssignment(xid=pid, xvid = __xvid)
                        )
                        # print("SV__XIVD_i",__xvid)
                        h_pid.update(xvariable_model.xvid.encode())
                        if i >0:
                            parent_child_relationship.append(
                                XVariableParentRelationshipDTO(**{"parent_id": items[i-1].get("xvid"),"child_id": __xvid })
                            )
                        xvariable_models.append(xvariable_model)
                    

                    create_parent_relationships_result = await self.xvar_parent_relatioship_service.create_many(parent_child_relationship)
                    if create_parent_relationships_result.is_err:
                        return create_parent_relationships_result

                    xvariable_model_seq  = XVariableDTO(
                        **e, 
                        xtype         = XType.Sequence,
                        value         = e.get("values"),
                        variable_type = XVariableType.Spatial,
                        raw           = product.ctx_vars.spatial_var,
                    )
                    xvar_assignments.append(XVariableAssignment(xid = pid, xvid = xvid ))
                    # print("SV__XIVD",xvid)
                    h_pid.update(xvid.encode())
                    xvariable_models.append(xvariable_model_seq)
                    result = await self.xvar_service.create_many(xvariable_models)
                else:
                    __type          = e.get("type")
                    __value         = e.get("value")
                    __xvid          = e.get("xvid")
                    # print("SV__XVID",__xvid)
                    h_pid.update(__xvid.encode())
                    xvariable_model = XVariableDTO(
                        **e,
                        variable_type=XVariableType.Spatial,
                        raw= f"{__type}({__value})"
                    )
                    # print("__XVID",__xvid)
                    xvar_assignments.append(XVariableAssignment(xid = pid, xvid = __xvid))
                    result = await self.xvar_service.create(xvariable_model)
            
            # print("XVAR_ASSIGNMENTS", xvar_assignments)

            # print("*"*40)
            tv_elements = tv.get("elements",[])
            # print("TV_ELEMENTS",tv_elements)
            tv_elements = sorted(tv_elements, key = lambda k: k["xvid"])
            for e in tv_elements:
                __type          = e.get("type")
                __value         = e.get("value")
                __xvid          = e.get("xvid")
                if __type == "DATE":
                    xvar = XVariableDTO(
                        **e,
                        variable_type= XVariableType.Temporal,
                        raw= f"{__type}({__value.month},{__value.day},{__value.year})"
                    )
                    # print("TV_XVAR_XVID_1",xvar.xvid)
                    h_pid.update(xvar.xvid.encode())
                    result = await self.xvar_service.create(xvar)
                    xvar_assignments.append(XVariableAssignment(xid = pid, xvid = __xvid))

                elif __type == "DATE_RANGE":
                    left_open  = e.get("left_open",False)
                    right_open = e.get("right_open",False)
                    left  = "(" if left_open else "["
                    right = ")" if right_open else "]"
                    start = e.get("start")
                    end   = e.get("end")
                    xvar = XVariableDTO(
                        xvid=__xvid,
                        type=__type,
                        value={
                            "start":start,
                            "end":end,
                            "left_open":left_open,
                            "right_open":right_open
                        },
                        xtype=XType.DateRange,
                        variable_type= XVariableType.Temporal,
                        raw=f"{left}Date({start.month}, {start.day}, {start.year}), Date({end.month}, {end.day}, {end.year}){right}"
                    )
                    # print("TV_XVAR_XVID",xvar.xvid)
                    h_pid.update(xvar.xvid.encode())
                    result = await self.xvar_service.create(xvar)
                    xvar_assignments.append(XVariableAssignment(xid = pid, xvid = __xvid))
                # print(e)

            # print("*"*40)
            iv_elements   = iv.get("elements")
            iv_elements = sorted(iv_elements, key = lambda k: k["xvid"])
            # print("IV_ELEMENTS",iv_elements)
            raws = []
            for e in iv_elements:
                __type = e.get("type")
                items = e.get("values")
                items = sorted(items, key = lambda k:k["xvid"])
                xvid   = e.get("xvid")
                xvars = []
                # __VALUES
                items_values = []
                for v in items:
                    _type = v.get("type")
                    _value = v.get("value")
                    _xvid = v.get("xvid")
                    raw = f"{_type}({_value})"
                    items_values.append(_value)
                    xvar = XVariableDTO(
                        **v,
                        variable_type=XVariableType.Interest,
                        raw=raw
                    )
                    # print("IV_XVAR_XVID",xvar.xvid)
                    h_pid.update(xvar.xvid.encode())
                    # print("_XVID",_xvid)
                    xvar_assignments.append(XVariableAssignment(xid = pid, xvid = _xvid))
                    raws.append(raw)
                    xvars.append(xvar)
                raws = sorted(raws, key = lambda k: k)
                if len(items) >1:
                    xvar_ = XVariableDTO(
                        xvid=xvid,
                        raw=",".join(raws),
                        type=__type,
                        value=items_values,
                        variable_type=XVariableType.Interest,
                        xtype=XType.Array
                    )
                    xvars.append(xvar_)
                    # print("*"*50)
                    # print("IV_XVAR_XVID>1",xvid)
                    # print("xVAR>1",xvar_)
                    # print("*"*50)
                    h_pid.update(xvid.encode())
                    xvar_assignments.append(XVariableAssignment(xid = pid, xvid = xvid))
                res = await self.xvar_service.create_many(xs = xvars)
            
            # print("*"*40)
            pt_elements   = pt.get("elements")
            pt_elements = sorted(pt_elements, key = lambda k: k["xvid"])
            # print("PT_ELEMENTS",pt_elements)
            for e in pt_elements:
                val  = e.get("value")
                xvid = e.get("xvid")
                xvar = XVariableDTO(
                    xvid          = xvid,
                    type          = e.get("type"),
                    raw           = f"{val}",
                    value         = val,
                    xtype         = XType.String,
                    variable_type = XVariableType.ProductType
                )
                h_pid.update(xvar.xvid.encode())
                await self.xvar_service.create(xvariable=xvar)
                xvar_assignments.append(XVariableAssignment(xid=pid, xvid = xvid))
            
            
            # print("*"*40)
            ov_elements   = ov.get("elements")
            ov_elements = sorted(ov_elements, key = lambda k: k["xvid"])
            # print("OV_ELEMENTS", ov_elements)
            for e in ov_elements:
                # print("e",e)
                value = e.get("value")
                event = value.get("event")
                method = value.get("method")
                scale = value.get("scale")
                xvid = e.get("xvid")
                xvar = XVariableDTO(**e, raw=f"{event}.{method}({scale})",variable_type=XVariableType.Observable)
                h_pid.update(xvar.xvid.encode())
                res = await self.xvar_service.create(xvariable=xvar)
                xvar_assignments.append(XVariableAssignment(xid = pid, xvid=xvid ))
            info_elements = info.get("elements")
            info_elements = sorted(info_elements, key = lambda k: k["xvid"])
            # event = info_elements.get("")
            # print("INFO",info)
            for e in info_elements:
                # print(e)
                event  = e.get('event')
                method = e.get("method")
                scale  = e.get("scale")
                stat   = e.get("stat")
                value  = e.get("value")
                xvid = e.get("xvid")
                xvar = XVariableDTO(
                    xvid=xvid,
                    type=f"{event}_{method}{'_'+scale if scale !=''else ''}",
                    xtype=XType.Object,
                    variable_type=XVariableType.Info,
                    value={
                        "event":event,
                        "method":method,
                        "scale":scale,
                        "stat":stat,
                        "value":value,
                    },
                    raw=f"{event}.{method}({scale}).[{','.join(raws)}].{stat}({value})"
                )
                h_pid.update(xvar.xvid.encode())
                h = H.sha256()
                h.update(stat.encode())
                xvid_stat = h.hexdigest()
                xvar_stat = XVariableDTO(
                    type=stat,
                    value=value,
                    variable_type=XVariableType.Info,
                    xvid=xvid_stat,
                    xtype=XType.String,
                    
                )
                res = await self.xvar_service.create_many([xvar, xvar_stat])
                xvar_assignments.append(XVariableAssignment(xid = pid, xvid =xvid ))
                xvar_assignments.append(XVariableAssignment(xid = pid, xvid =xvid_stat ))
            pid = h_pid.hexdigest()
            # print("PID",pid)
            for xass in xvar_assignments:
                xass.xid = pid
            res = await self.xvar_assignments_service.create_many(dtos = xvar_assignments)
            # print("RESUILT",res)
            res = await self.create_product(
                product= ProductModel(
                    pid            = pid,
                    content_vars   = ContentVars(**product.content_vars.model_dump()),
                    ctx_vars       = ContextualVars(**product.ctx_vars.model_dump()),
                    data_source_id = product.data_source_id,
                    data_view_id   = product.data_view_id,
                    description    = product.description,
                    disabled       = False,
                    name           = product.name,
                    plot_desc      = PlotDescription(**product.plot_desc.model_dump())
                )
            )
            print("PRODUCT_RESULT",res)
            # xvar_assignments = map(lambda x:x, xvar_assignments)
        except Exception as e:
            print("ERROR", e)
            return Err(e)
    async def create_product(self, product:ProductModel)->Result[str,JubError]:
        try:
            exists = await self.exists(pid = product.pid)
            if exists:
                return Err(AlreadyExists(detail="Product already exists."))
            res = await self.repo.create(product=product)
            if res.is_err:
                return Err(UnknownError(str(res.unwrap_err())))
            return res
        except Exception as e:
            return Err(e)
    async def exists(self, pid:str)->bool:
        try:
            res = await self.repo.exists_by_pid(pid= pid)
            return res
        except Exception as e:
            return Err(e)
    # async def __createx(self, product: ProductCreationDTO) -> Result[str, OcaError]:
    #     try:
    #         sv_result = SVResult(**parse_sv(f"SV={product.ctx_vars.spatial_var}").asDict().get("sv"))
    #         tv_result = TVResult(**parse_tv(f"TV={product.ctx_vars.temporal_var}").asDict().get("tv"))
    #         iv_result = IVResult(**parse_iv(f"IV={product.content_vars.interest_var}").asDict().get("iv"))
    #         pt_result = PTResult(**parse_pt(f"ProductType={product.ctx_vars.product_type}").asDict().get("pt"))
            
    #         pid = ""
    #         h_pid = H.sha256()
    #         sv_assignments,sv_xvar_models, h_pid = ProductsService.__sv_assignments(h_pid=h_pid, elements=sv_result.elements)
    #         # print(sv_xvar_models)
    #         # _____________________________A
    #         # TV ASSIGMENTS
    #         tv_assigments,tv_xvar_models,h_pid = ProductsService.__tv_assignments(h_pid=h_pid, elements=tv_result.elements)
    #         # print(tv_xvar_models)
    #         #  IV ASSIGMENTS
    #         iv_assigments,iv_xvar_models,h_pid = ProductsService.__iv_assignments(h_pid=h_pid, elements=iv_result.elements)
    #         # print("IV_MODELS",iv_xvar_models)
    #         pt_assignments,pt_xvar_models,h_pid = ProductsService.__pt_assignments(h_pid=h_pid, elements=pt_result.elements)
    #         # print("PT_MODELS",pt_xvar_models)
    #         # print("PT_ASSIGMENTS", pt_assignments)
    #         pid = h_pid.hexdigest()
            
    #         assignments = sv_assignments + tv_assigments + iv_assigments + pt_assignments
    #         assignments_with_error:List[XVariableAssignment]  = []
    #         xvar_models = sv_xvar_models + tv_xvar_models + iv_xvar_models + pt_xvar_models

    #         xvar_with_error:List[XVariableModel] = []
    #         for xvar_model in  xvar_models:
    #             exists = await self.xvar_repo.exists_by_xvid(xvid=xvar_model.xvid)
    #             if exists:
    #                 continue
    #             res = await self.xvar_repo.create(variable=xvar_model)
    #             if res.is_err:
    #                 xvar_with_error.append(xvar_model)
            
    #         if len(xvar_models) == len(xvar_with_error):
    #             xvar_with_error = []

    #         for x in assignments:
    #             x.xid = pid
    #             exists = await self.xvar_assignments_repo.exists_by_xid_and_xvid(xid=x.xid, xvid=x.xvid)
    #             if not exists:
    #                 res = await self.xvar_assignments_repo.create(x)
    #                 if res.is_err:
    #                     print(x,res, "Failed to save")
    #                     assignments_with_error.append(x)
    #         if len(assignments_with_error) == len(assignments):
    #             assignments_with_error = []
            
    #         product_model = ProductModel(
    #             pid            = pid,
    #             name           = product.name,
    #             description    = product.description,
    #             data_source_id = product.data_source_id,
    #             data_view_id   = product.data_view_id,
    #             content_vars   = ContentVars(**product.content_vars.model_dump()),
    #             ctx_vars       = ContextualVariables(**product.ctx_vars.model_dump()),
    #             plot_desc      = PlotDescription(**product.plot_desc.model_dump()),
    #             disabled       = False,
    #         )
    #         product_exists = await self.repo.exists_by_pid(pid=pid)
    #         if not product_exists:
    #             result = await self.repo.create(product=product_model)
    #             if result.is_err:
    #                 return Err(UknownError(detail=str(result.unwrap_err())))
    #         return Ok(pid)
    #     except Exception as e:
    #         return Err(e)
    # async def create(self, product: ProductCreationDTO) -> Result[str, OcaError]:
    #     try:
    #         if product.pid  == "":
    #             product.pid = nanoid(alphabet=self.obid_aphabet, size=self.obid_size)
    #         exists = await self.repo.find_by_pid(pid= product.pid)
    #         if exists.is_ok:
    #             return Err(AlreadyExists("Product already exists."))
    #         product_model = ProductModel(
    #             pid            = ,
    #             name           = product.name,
    #             description    = product.description,
    #             data_source_id = product.data_source_id,
    #             data_view_id   = product.data_view_id,
    #             content_vars   = ContentVars(**product.content_vars),
    #             ctx_vars       = ContextualVariables(**product.ctx_vars),
    #             plot_desc      = PlotDescription(**product.plot_desc),
    #             disabled       = False,
    #         )
    #         # model = ProductModel(**product.model_dump())
    #         x = await self.repo.create(model)
    #         return Ok(product.pid)
    #     except Exception as e:
    #         return Err(e)
    


class XVariableAssignmentsService:
    def __init__(self, repo: XVariableAssignmentRepository):
        self.repo = repo

    async def create(self, dto:XVariableAssignment)->Result[str,JubError]:
        try:
            exists = await self.exists(xid=dto.xid, xvid= dto.xvid)
            
            if exists:
                return Err(AlreadyExists(detail="XVariable assignement exists."))

            result = await self.repo.create(x=dto)

            if result.is_err:
                return Err(UnknownError(result.unwrap_err()))

            return result
        
        except Exception as e:
            return Err(e)
    async def create_many(self, dtos:List[XVariableAssignment])->Result[int, JubError]:
        try:
            async def __inner(dto:XVariableAssignment):
                exists = await self.repo.exists_by_xid_and_xvid(xid = dto.xid, xvid=dto.xvid)
                return exists, dto
            xs            = await asyncio.gather(*list(map(lambda x:__inner(x), dtos)))
            filtered_dtos = list(map(lambda x: x[1] , filter(lambda x: not x[0], xs) ))
            if len(filtered_dtos) == 0:
                return Ok(0)
            res = await self.repo.create_many(xs = filtered_dtos)
            if res.is_err:
                return Err(UnknownError(res.unwrap_err()))
            n = len(res.unwrap())
            return Ok(n)

        except Exception as e:
            return Err(e)
    async def exists(self, xid:str, xvid:str)->bool:
        try:
            res = await self.repo.exists_by_xid_and_xvid(xid=xid, xvid=xvid)
            return res
        except Exception as e:
            return Err(e)
    async def assign(self,dto:MultipleXVariableAssignmentDTO)->Result[List[str],JubError]:
        try:
            xid = dto.xid
            xvids = []
            for assignment in dto.assignments:
                h = H.sha256()
                x = f"{assignment.kind}{assignment.value}"
                h.update(x.encode("utf-8"))
                xvid = h.hexdigest()
                xvids.append(XVariableAssignment(xid=xid, xvid=xvid))
            res = await self.repo.create_many(xs=xvids)
            if res.is_err:
                return Err(UnknownError(detail=str(res.unwrap_err())))
            return res
        except Exception as e:
            return Err(e)

