# Mini-Youtube-microservice2
Microservice 2 of the Mini-Youtube Project. Login Service.

Member Login and Administrator Login.

register 

curl -X POST http://ec2-3-128-95-160.us-east-2.compute.amazonaws.com:1024/register/   -H "Content-Type: application/json"  -d "{\"email\":\"zhongyuanye2000@gmail.com\"}"

verify

curl -X POST http://ec2-3-128-95-160.us-east-2.compute.amazonaws.com:1024/verify/   -H "Content-Type: application/json"   -d "{\"email\":\"zhongyuanye2000@gmail.com\", \"code\":\"5b0af0df-7e68-4ad9-9ddc-64f09072f78a\"}"

login

curl -X POST http://ec2-3-128-95-160.us-east-2.compute.amazonaws.com:1024/login/   -H "Content-Type: application/json"     -d "{\"email\":\"zhongyuanye2000@gmail.com\"}"

login-verify

curl -X POST http://ec2-3-128-95-160.us-east-2.compute.amazonaws.com:1024/verify-login/  -H "Content-Type: application/json"  -d "{\"email\":\"zhongyuanye2000@gmail.com\", \"code\":\"86ebc279-c9a4-44b8-9239-9763844837b6\"}"

