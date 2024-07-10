from fastapi import FastAPI, HTTPException, Request, Header, Depends
import logging
import os
from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field
import motor.motor_asyncio
from bson import ObjectId
import networkx as nx
from fastapi.security import OAuth2PasswordBearer

# 로깅 설정
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

# MongoDB 설정
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb+srv://<username>:<password>@cluster0.mongodb.net/mydatabase?retryWrites=true&w=majority")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
db = client.mydatabase  # 실제 데이터베이스 이름으로 변경

# OAuth2 설정
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# 모델 정의
class User(BaseModel):
    kakaoId: str
    profile_nickname: str
    profile_image: str

    class Config:
        json_encoders = {ObjectId: str}
        arbitrary_types_allowed = True

class Group(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    name: str
    profile_image: Optional[str] =""
    members: List[str] = []

    class Config:
        json_encoders = {ObjectId: str}
        arbitrary_types_allowed = True

class Debt(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    from_user: str
    to_user: str
    amount: int
    description: str
    group: Optional[str] = None #group_id
    settled: bool = False
    date: str
    expense: str

    class Config:
        json_encoders = {ObjectId: str}
        arbitrary_types_allowed = True

class ExpenseParticipant(BaseModel):
    user: str
    amount: int
    settled: bool = False

class Expense(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    amount: int
    description: str
    payer: str
    group: Optional[str] = None
    participants: List[ExpenseParticipant] = []
    settled: bool = False
    date: str
    type: str

    class Config:
        json_encoders = {ObjectId: str}
        arbitrary_types_allowed = True

class DebtBalance(BaseModel):
    kakao_id: str
    profile_nickname: str
    balance: int

class KakaoUserRequest(BaseModel):
    kakaoId: str
    profile_nickname: str
    profile_image: str

class GroupDebtSummary(BaseModel):
    groupId: str
    name: str
    totalDebt: int
    profile_image: Optional[str] = ""
    members_id: List[str] = []
    members_nickname: List[str] = []


# Kakao 사용자 정보를 받아 처리하는 엔드포인트
@app.post("/kakao-login", response_model=User)
async def kakao_login(user_info: KakaoUserRequest):
    kakao_id = user_info.kakaoId
    profile_nickname = user_info.profile_nickname
    profile_image = user_info.profile_image

    # 사용자 데이터베이스에서 사용자 검색
    user = await db.users.find_one({"kakaoId": kakao_id})
    
    # 사용자가 존재하지 않는 경우 새로운 사용자 추가
    if not user:
        new_user = User(
            kakaoId=kakao_id,
            profile_nickname=profile_nickname,
            profile_image=profile_image
        )
        await db.users.insert_one(new_user.model_dump(by_alias=True))
        logger.info(f"새 사용자 {kakao_id}이(가) 데이터베이스에 추가되었습니다")
        return new_user

    logger.info(f"기존 사용자 {kakao_id}이(가) 로그인하였습니다")
    return User.construct(**user)

# 사용자 목록을 반환하는 엔드포인트
@app.get("/users", response_model=List[User])
async def get_users():
    users = await db.users.find().to_list(length=None)
    return [User.construct(**user) for user in users]

# 사용자 관련 엔드포인트
@app.get("/users/{kakao_id}", response_model=User)
async def get_user(kakao_id: str):
    user = await db.users.find_one({"kakaoId": kakao_id})
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return User.construct(**user)

@app.put("/users/{kakao_id}", response_model=User)
async def update_user(kakao_id: str, user: User):
    await db.users.update_one({"kakaoId": kakao_id}, {"$set": user.model_dump(by_alias=True)})
    updated_user = await db.users.find_one({"kakaoId": kakao_id})
    return User.construct(**updated_user)


# 채무 내역 조회 엔드포인트
@app.get("/debts/{kakao_id}/balance", response_model=List[DebtBalance])
async def get_user_debts_balance(kakao_id: str):
    logger.debug(f"Fetching user for kakao_id: {kakao_id}")
    user = await db.users.find_one({"kakaoId": kakao_id})
    
    if not user:
        logger.debug(f"No user found for kakao_id: {kakao_id}")
        raise HTTPException(status_code=404, detail="User not found")

    profile_nickname = user["profile_nickname"]
    logger.debug(f"Fetching debts for user with profile_nickname: {profile_nickname}")
    user_debts = await db.debts.find({"$or": [{"from_user": profile_nickname}, {"to_user": profile_nickname}]}).to_list(length=None)
    logger.debug(f"Found debts: {user_debts}")

    if not user_debts:
        logger.debug(f"No debts found for user with profile_nickname: {profile_nickname}")
        return []

    balance = {}
    for debt in user_debts:
        other_user = debt["to_user"] if debt["from_user"] == profile_nickname else debt["from_user"]
        if other_user not in balance:
            balance[other_user] = 0
        balance[other_user] += debt["amount"] if debt["from_user"] == profile_nickname else -debt["amount"]

    response = []
    for other_user_nickname, amount in balance.items():
        other_user = await db.users.find_one({"profile_nickname": other_user_nickname})
        response.append(DebtBalance(
            kakao_id=other_user["kakaoId"] if other_user else "Unknown",
            profile_nickname=other_user_nickname,
            balance=amount
        ))
    
    logger.debug(f"Response: {response}")
    return response



# 채무 관계 단순화를 위한 헬퍼 함수
async def simplify_debts(group_name: str):
    debts = await db.debts.find({"group": group_name}).to_list(length=None)

    if not debts:
        logger.debug(f"No debts found for group name: {group_name}")
        return

    balance = {}
    for debt in debts:
        from_user = debt["from_user"]
        to_user = debt["to_user"]
        amount = debt["amount"]

        if from_user not in balance:
            balance[from_user] = 0
        if to_user not in balance:
            balance[to_user] = 0

        balance[from_user] -= amount
        balance[to_user] += amount

    # 새로운 단순화된 채무 목록 생성
    new_debts = []
    positive_balances = {user: amt for user, amt in balance.items() if amt > 0}
    negative_balances = {user: -amt for user, amt in balance.items() if amt < 0}

    for to_user, amount in positive_balances.items():
        while amount > 0:
            from_user, from_amount = next(iter(negative_balances.items()))
            if amount >= from_amount:
                new_debts.append({
                    "from_user": from_user,
                    "to_user": to_user,
                    "amount": from_amount,
                    "description": "Simplified debt",
                    "group": group_name,
                    "settled": False,
                    "date": datetime.now().strftime('%Y-%m-%d'),
                    "expense": ""
                })
                amount -= from_amount
                del negative_balances[from_user]
            else:
                new_debts.append({
                    "from_user": from_user,
                    "to_user": to_user,
                    "amount": amount,
                    "description": "Simplified debt",
                    "group": group_name,
                    "settled": False,
                    "date": datetime.now().strftime('%Y-%m-%d'),
                    "expense": ""
                })
                negative_balances[from_user] -= amount
                amount = 0

    # 기존 채무 삭제 및 새로운 단순화된 채무 추가
    await db.debts.delete_many({"group": group_name})
    if new_debts:
        await db.debts.insert_many(new_debts)
        logger.debug(f"Inserted new simplified debts: {new_debts}")

# 그룹 ID를 받아서 채무 관계를 단순화하는 엔드포인트
@app.post("/groups/{group_id}/simplify-debts")
async def simplify_group_debts(group_id: str):
    logger.debug(f"Simplifying debts for group with ID: {group_id}")
    group = await db.groups.find_one({"_id": group_id})

    if not group:
        logger.error(f"Group with ID {group_id} not found")
        raise HTTPException(status_code=404, detail="Group not found")

    group_name = group["name"]
    logger.debug(f"Group found: {group} with name: {group_name}")

    await simplify_debts(group_name)
    return {"message": "Debts simplified successfully"}




# 사용자가 속한 그룹에서의 채무 총액 조회 엔드포인트
@app.get("/debts/{kakao_id}/groups", response_model=List[GroupDebtSummary])
async def get_user_debts_groups(kakao_id: str):
    user_groups = await db.groups.find({"members": kakao_id}).to_list(length=None)
    group_debts = []
    for group in user_groups:
        group_debt = await db.debts.find({"group": str(group["_id"]), "$or": [{"from_user": kakao_id}, {"to_user": kakao_id}]}).to_list(length=None)
        total_debt = sum(debt["amount"] if debt["from_user"] == kakao_id else -debt["amount"] for debt in group_debt)

        members_id = group["members"]
        members_nickname = []

        for member_id in members_id:
            member = await db.users.find_one({"kakaoId": member_id})
            if member:
                members_nickname.append(member["profile_nickname"])
            else:
                members_nickname.append("Unknown")

        group_debts.append(GroupDebtSummary(
            groupId=str(group["_id"]),
            name=group["name"],
            totalDebt=total_debt,
            profile_image=group.get("profile_image", ""),
            members_id=members_id,
            members_nickname=members_nickname
        ))
    return group_debts




#특정 사람과의 debts 가져오기
@app.get("/debts/{kakao_id}/{person_kakao_id}", response_model=List[Debt])
async def get_debts_with_person(kakao_id: str, person_kakao_id: str):
    logger.debug(f"Fetching debts between {kakao_id} and {person_kakao_id}")

    # 사용자 프로필 닉네임 조회
    user = await db.users.find_one({"kakaoId": kakao_id})
    person = await db.users.find_one({"kakaoId": person_kakao_id})

    if not user or not person:
        raise HTTPException(status_code=404, detail="User not found")

    user_nickname = user['profile_nickname']
    person_nickname = person['profile_nickname']

    logger.debug(f"User nickname: {user_nickname}, Person nickname: {person_nickname}")

    # 프로필 닉네임으로 debts 조회
    debts_with_person = await db.debts.find({"$or": [
        {"from_user": user_nickname, "to_user": person_nickname},
        {"from_user": person_nickname, "to_user": user_nickname}
    ]}).to_list(length=None)

    # _id를 문자열로 변환
    for debt in debts_with_person:
        debt["_id"] = str(debt["_id"])

    logger.debug(f"Debts found: {debts_with_person}")
    return [Debt.construct(**debt) for debt in debts_with_person]







#해당 그룹의 모든 expenses 가져오기
@app.get("/expenses/{groupId}", response_model=List[Expense])
async def get_expenses_by_group(groupId: str):
    logger.debug(f"Fetching expenses for group with ID: {groupId}")
    group = await db.groups.find_one({"_id": groupId})

    if not group:
        logger.error(f"Group with ID {groupId} not found")
        raise HTTPException(status_code=404, detail="Group not found")

    group_name = group["name"]
    logger.debug(f"Group found: {group} with name: {group_name}")

    expenses_in_group = await db.expenses.find({"group": group_name}).to_list(length=None)
    logger.debug(f"Expenses found with group name {group_name}: {expenses_in_group}")

    return [Expense.construct(**expense) for expense in expenses_in_group]




# 지출 내역 조회 엔드포인트
@app.get("/expenses/{expense_id}", response_model=Expense)
async def get_expense(expense_id: str):
    expense = await db.expenses.find_one({"_id": ObjectId(expense_id)})
    if expense is None:
        raise HTTPException(status_code=404, detail="Expense not found")
    return Expense.construct(**expense)



# 특정 그룹의 모든 지출 내역 조회 엔드포인트
@app.get("/expenses/group/{group_id}", response_model=List[Expense])
async def get_group_expenses(group_id: str):
    group_expenses = await db.expenses.find({"group": ObjectId(group_id)}).to_list(length=None)
    return [Expense.construct(**expense) for expense in group_expenses]



# 지출 내역 추가 엔드포인트
@app.post("/expense", response_model=Expense)
async def create_expense(expense: Expense):
    new_expense = await db.expenses.insert_one(expense.model_dump(by_alias=True))
    created_expense = await db.expenses.find_one({"_id": new_expense.inserted_id})
    await update_debts_for_expense(created_expense)
    return Expense.construct(**created_expense)

async def update_debts_for_expense(expense):
    for participant in expense['participants']:
        if participant['user'] != expense['payer']:
            new_debt = Debt(
                from_user=participant['user'],
                to_user=expense['payer'],
                amount=participant['amount'],
                description=expense['description'],
                group=expense.get('group'),
                settled=participant['settled'],
                date=expense['date'],
                expense=str(expense['_id'])
            )
            await db.debts.insert_one(new_debt.model_dump(by_alias=True))

# 지출 내역 삭제 엔드포인트
@app.delete("/expenses/{expense_id}", response_model=dict)
async def delete_expense(expense_id: str):
    result = await db.expenses.delete_one({"_id": ObjectId(expense_id)})
    if result.deleted_count == 1:
        await delete_debts_for_expense(expense_id)
        return {"message": "Expense deleted"}
    raise HTTPException(status_code=404, detail="Expense not found")

async def delete_debts_for_expense(expense_id):
    await db.debts.delete_many({"expense": expense_id})

# 그룹 추가 엔드포인트
@app.post("/groups", response_model=Group)
async def create_group(group: Group):
    new_group = await db.groups.insert_one(group.model_dump(by_alias=True))
    created_group = await db.groups.find_one({"_id": new_group.inserted_id})
    return Group.construct(**created_group)

# 채무 추가 엔드포인트
@app.post("/debts", response_model=Debt)
async def create_debt(debt: Debt):
    new_debt = await db.debts.insert_one(debt.model_dump(by_alias=True))
    created_debt = await db.debts.find_one({"_id": new_debt.inserted_id})
    return Debt.construct(**created_debt)



#정산 엔드포인트
@app.post("/delete/{kakao_id}/{person_kakao_id}")
async def delete_debts_between_users(kakao_id: str, person_kakao_id: str):
    logger.debug(f"Deleting debts between {kakao_id} and {person_kakao_id}")

    # 사용자 프로필 닉네임 조회
    user = await db.users.find_one({"kakaoId": kakao_id})
    person = await db.users.find_one({"kakaoId": person_kakao_id})

    if not user or not person:
        raise HTTPException(status_code=404, detail="User not found")

    user_nickname = user['profile_nickname']
    person_nickname = person['profile_nickname']

    logger.debug(f"User nickname: {user_nickname}, Person nickname: {person_nickname}")

    # 두 사용자 사이의 모든 debts 삭제
    delete_result = await db.debts.delete_many({"$or": [
        {"from_user": user_nickname, "to_user": person_nickname},
        {"from_user": person_nickname, "to_user": user_nickname}
    ]})

    logger.info(f"Deleted {delete_result.deleted_count} debts between {user_nickname} and {person_nickname}")
    return {"message": f"Deleted {delete_result.deleted_count} debts between {user_nickname} and {person_nickname}"}



# 루트 엔드포인트
@app.get("/")
async def read_root(request: Request):
    logger.info(f"{request.client.host}에서 요청을 받았습니다")
    return {"message": "Hello World"}

# 애플리케이션 실행
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")
