"""
schema.py - the fixed "form" the AI must fill when it reads a rating report.
Pydantic checks the AI's answer matches this form, so we never get random text back.
Money values are in INR crore, exactly as written in the report.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class FinancialYear(BaseModel):
    year: str = Field(description="Financial year label, e.g. 'FY24' or 'March 2024'")
    revenue: Optional[float] = Field(None, description="Total operating income / revenue")
    ebitda: Optional[float] = Field(None, description="EBITDA / operating profit")
    net_profit: Optional[float] = Field(None, description="Profit after tax (PAT)")
    total_debt: Optional[float] = Field(None, description="Total debt / total borrowings")
    net_worth: Optional[float] = Field(None, description="Tangible net worth / shareholders' equity")
    interest_expense: Optional[float] = Field(None, description="Interest / finance cost")


class CreditReport(BaseModel):
    company_name: str
    agency: Optional[str] = Field(None, description="Rating agency: CARE, CRISIL, ICRA, India Ratings, Acuite...")
    rating: Optional[str] = Field(None, description="Assigned rating, e.g. 'AA-'")
    outlook: Optional[str] = Field(None, description="Stable / Positive / Negative / Watch")
    report_date: Optional[str] = None
    strengths: List[str] = Field(default_factory=list, description="Key credit strengths, short phrases")
    risks: List[str] = Field(default_factory=list, description="Key credit risks / weaknesses, short phrases")
    financials: List[FinancialYear] = Field(default_factory=list, description="One entry per year, oldest first")
