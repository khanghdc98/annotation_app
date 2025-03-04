# Ứng dụng hỗ trợ dán nhãn Egocentric Action Recognition cho tập dữ liệu Lifelog

## Giới thiệu

**Lifelog**: Hành động thu thập, ghi chép dữ liệu về cuộc sống hằng ngày của bản thân. Trong ngữ cảnh của ứng dụng này, dữ liệu lifelog là dữ liệu hình ảnh được thu thập từ wearable camera.

**Egocentric Action Recognition**: Dự đoán hành động được thực hiện bởi người dùng, từ hình ảnh được chụp từ góc nhìn của họ.

---

## Dataset
- Được thu thập từ một giáo sư người Ireland trong thời gian từ 01/2019 - 06/2020.
- Gồm dữ liệu ảnh của ~530 ngày, mỗi ngày khoảng 1000-2000 hình ảnh.
- Tổng số lượng ảnh: ~725k.
- Kích thước bộ dữ liệu: ~55GB.
- **Link**: ... *(link riêng tư, liên hệ chủ project để tải về)*

### Cấu trúc thư mục:
```
201901/
    01/
        20190101_103717_000.jpg
        20190101_103749_000.jpg
        *.jpg
        ...
    02/
    03/
    ...
    31/
201902/
201903/
...
202006/
```

**Danh sách labels**: Xem ở `unique_new_labels.json`

---

## Hướng dẫn cài đặt

1. `git clone ...`
2. `python main/app.py`

## Yêu cầu chung
- Mỗi ảnh có đúng **1 main action** và tối đa **1 concurrent action**. Main action là hành động chính, nổi bật trong bức ảnh, concurrent action là hành động diễn ra đồng thời với main action, có tầm quan trọng thấp hơn.
- Action label của 1 hình ảnh có thể được dùng để dán nhãn đồng loạt (**propagate**) cho nhiều hình ảnh tương đồng trong tập dữ liệu (**tối thiểu 10, tối đa 30**).
- Xuất file output theo format: `yyyymmdd.csv`

### Một số quy tắc:
- Theo dòng thời gian, hành động A đang diễn ra lâu dài, liên tục thì hành động B xuất hiện trong một giai đoạn ngắn, song song với giai đoạn A.
  - **Ảnh chỉ có A**: A là **main action**.
  - **Ảnh có cả A và B**: B là **main action**, A là **concurrent action**.
  - **Ví dụ**:
    <div style="display: flex; justify-content: center;">
      <img src="img/20191031_135054_000.jpg" width="200px" style="margin-right: 10px;">
      <img src="img/20191031_135325_000.jpg" width="200px" style="margin-right: 10px;">
      <img src="img/20191031_135359_000.jpg" width="200px">
    </div>
    
    ```
    | Hình ảnh | Main Action | Concurrent Action |
    |--------------------------|-------------|-------------------|
    | Ảnh 1	               | attending a presentation sách    |                   |
    | Ảnh 2  	               | using computer | attending a presentation          |
    | Ảnh 3		       | attending a presentation |           |
    ```
- Các ảnh được propagate phải có **main action và concurrent action (nếu có)** giống hoàn toàn với ảnh ban đầu.

### Một số trường hợp đặc biệt
*(Bổ sung nội dung tại đây nếu cần)*

---

## Hướng dẫn sử dụng
*(Bổ sung nội dung hướng dẫn sử dụng tại đây)*

