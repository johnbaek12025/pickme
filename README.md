# PickMe

## 1. 프로그램 설명
#### - DB에서 쿠팡 상품 검색을 위한 키워드와 vendoritemid를 가져와서<br> &nbsp; 쿠팡 메인페이지에서 검색, 페이징을 통해 해당 상품 링크에 packet 통신을 하는 프로그램<br><br>
## 2. 프로그램 구성
####  1.구성은 bin/mn.py 실행을 통해 mine/control_manager.py에 config 파일의 정보를 전달 <br>2.mine/db_manager.py에서 config.cfg정보에 따른 DB에 연결 <br>3.DB에서 검색할 keyword 및 vendoritemid를 가져와서 현재IP주소로 해당 검색 키워드및 &nbsp;&nbsp;vendoritemid를 검색한 이력이 있는지 확인 <br>4.검색 이력이 있으면 ip주소를 다시 변경하여 검색이력이 없는 ip로 바뀔 때까지 반복 검색 &nbsp;&nbsp;&nbsp;이력이 없으면 다음 진행<br> 5.mine/pickme.py에서 packet통신 main_page→검색→페이징→상품url수집&nbsp;→urlpacket통신<br>6.현재IP, 검색키워드, vendoritemid를 db에 저장
<br>

## 3.발생된 문제
#### - pymysql.err.OperationalError 예외<br>&nbsp;&nbsp;mine/control_manager.py에서<br>&nbsp;&nbsp;ControlManager class의 check_log method에서 ip변경시마다<br>&nbsp;&nbsp;DB연결이&nbsp;OperationalError발생하면서 프로그램이 중지되는 현상 발생<br>&nbsp;&nbsp;처음에는 OperationalError 예외 발생시 일정 시간을 두고 재시도 하는 식으로 코드를 변경
```python
def check_log(self, log):   
        sql = f"""
        select  *
        from 	wooriq.cp_searchlog
        where   Keyword = "{log['keyword']}"
        and     ProductID = "{log['ProductID']}"
        and     IP_Address = "{log['ip_address']}"
        """
        try:
            got_data = self.wooriq_db.get_all_rows(sql)
        except OperationalError:
            time.sleep(60)
            got_data = self.wooriq_db.get_all_rows(sql)
            
        if not len(got_data):
            return log['ip_address']
        else:
            ip_address = switchIp2()
            if not ip_address:
                raise IPChangeError
            log['ip_address'] = ip_address
            return self.check_log(log)
```
####  그러나 이번에는 pymysql.err.InterfaceError가 발생해서 해결이 되지 않았다.<br>문제는 예외를 잡아내는 것이 아니라 IP변경으로 인해 DB연결이 중단되는 문제 발생<br><br><strong>[해결 방법](https://community.oracle.com/tech/developers/discussion/547342/how-change-in-ip-address-affects-the-application-server-and-database-server)</strong><br><em>위 링크에 따르면 ip변경시마다 DB연결을 다시 해주면 된다고 한다.</em>
```python
ip_address = switchIp2()
self.connect_to_db()
```
#### &nbsp;<em>ip변경시마다 connect_to_db method를 call함으로서 문제 해결</em>
<br><br>

## 4. 실행
#### 1. pip install -r requirements.txt<br>2. exemple폴더의 exem.cfg파일을 작성<br>3. /bin에서 python mn.py --config=../cfg/config.cfg 실행


#cor

## 1. 프로그램 설명
### - 기존 동기화 방식에서 DB에서 data를 가져와서 해당 데이터의 상품을 targeting에서 API방식으로 변환을 하여 매 한 시간 마다 해당 데이터를 갱신하는 방식으로 변환 하여 API 접속량을 줄이고, 동기화 방식에서 찾은 방식을 python asyncio 및 aiohttp를 이용해서 비동기 방식으로 적용

## 2. 프로그램 구성
####1. main.py - 비동기 프로세스 전반적인 통제<br>2. slotdata.py - 각 상품의 객체 list 생성 및 무작위 순서 적용<br>traffic.py - 유효 트래픽 처리를 위한 세부적인 단계 관리<br>trafficlog.py - traffic.py에서 각 단계별 logging 관리<br>ip.py - tethering을 통한 ip변경

## 4. 실행
#### #### 1. pip install -r requirements.txt<br>/cor 폴더에서 python main.py --config=../cfg/config.cfg 실행
