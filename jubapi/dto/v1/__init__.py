from typing import Optional,List
from pydantic import BaseModel

    

class InequalityFilter(BaseModel):
    gt: Optional[int] = None  # Greater than
    lt: Optional[int] = None  # Less than
    eq: Optional[int] = None  # Equal to


class InterestFilter(BaseModel):
    # Allow either a simple value (str) or an inequality filter
    value: Optional[str] = None
    inequality: Optional[InequalityFilter] = None

  
    
class  TemporalFilter(BaseModel):
    low: int
    high: int

class SpatialFilter(BaseModel):
    country: str
    state: str
    municipality: str
    def make_regex(self):
        
        x = ""
        if self.country == "*":
            x+=".*"
        else:
            x+= self.country+"\\."
        
        if self.state == "*":
            x+=".*"
        else:
            x+= "{}".format(self.state)
        
        if self.municipality == "*":
            x+=".*"
        else:
            x+= "{}".format(self.municipality)
            
        return x.upper()
        # return "{}|{}|{}".format(self.country, self.state,self.municipality).upper()
        # x = "^"
        # if self.country =="*":
        #     x +=".*\\"
        # else:
        #     x += "{}".format(self.country)
        
        # if self.state =="*":
        #     x +="\\..*"
        # else:
        #     x += "\\.{}".format(self.state)
        # if self.municipality =="*":
        #     x +="\\.*"
        # else:
        #     x += "\\.{}".format(self.municipality)
        # return x.upper()
        

        # return "{}".format()



class ProductFilter(BaseModel):
    temporal: Optional[TemporalFilter] = None
    spatial: Optional[SpatialFilter] = None
    interest: List[InterestFilter]=[]
    tags:List[str] = []