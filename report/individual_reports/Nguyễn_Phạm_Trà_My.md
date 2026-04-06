# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Nguyễn Phạm Trà My**:
- **2A202600482**:
- **06/04/2026**:

---

## I. Technical Contribution (15 Points)

- **Modules Implementated**: [`src/tools/search.py`,'src/core/gemini_provider.py','src/agent/agent.py']
- **Code Highlights**: [Dynamic Search Tool (src/search.py) 
def search_with_llm(args_str: str, llm: LLMProvider) -> str:
    system_prompt = "You are an expert curriculum search engine. Return a numbered list (max 5 points)."
    result_dict = llm.generate(prompt=f"Search query: '{args_str}'", system_prompt=system_prompt)
    return result_dict["content"].strip()]
- **Documentation**: [Khi nhận được yêu cầu từ user,Agent đi qua chuỗi logic: Though(Phân tích nhu cầu) -> Action (Gọi hàm search) -> Observation(Nhận dữ liệu từ môi trường). Quá trình này sẽ được lặp lại đến khi Agent thu thập đủ thông tin để lập kế hoạch chi tiết]

---

## II. Debugging Case Study (10 Points)

_Analyze a specific failure event you encountered during the lab using the logging system._

- **Problem Description**: [Agent gặp lỗi ngắt quãng chu trình ReAct với thông báo Parsing failed. Mặc dù LLM đã tìm ra câu trả lời cuối cùng chính xác, nhưng hệ thống không thể bóc tách kết quả để hiển thị cho người dùng, dẫn đến việc Agent báo lỗi thay vì kết thúc nhiệm vụ thành công.]
- **Log Source**: [{"timestamp": "2026-04-06T08:27:28.230456", "event": "AGENT_ERROR", "data": {"error": "Parsing failed", "text": "Final Answer: I have found some basic Machine Learning study materials for you, including a course by Andrew Ng, a book by Aur\u00e9lien G\u00e9ron, and a YouTube playlist from MIT OpenCourseWare. Based on the current date, you have 10 days until the end of this month. I have scheduled a 2-hour daily practical study session for Machine Learning from now until the end of the month, which has been successfully added to your Google Calendar."}}]
- **Diagnosis**: [Nguyên nhân chính là sự không nhất quán giữa định dạng phản hồi của LLM và bộ lọc Regular Expression (Regex) trong mã nguồn agent.py.

LLM đã gộp chung câu trả lời cuối cùng vào một khối văn bản dài mà không có các ký tự ngắt dòng (newline) hoặc cấu trúc phân tách rõ ràng như yêu cầu trong System Prompt.

Hệ thống ReAct Loop không tìm thấy từ khóa Action: để đi tiếp, đồng thời Regex hiện tại cũng thất bại trong việc nhận diện từ khóa Final Answer: khi nó bị bao quanh bởi quá nhiều văn bản tự do.]
- **Solution**: [Cập nhật Prompt: Siết chặt yêu cầu về định dạng đầu ra trong get_system_prompt, buộc LLM phải sử dụng cấu trúc Final Answer: <content> trên một dòng riêng biệt.

Tối ưu hóa Regex: Cấu hình lại bộ lọc Regex trong run() để có thể xử lý linh hoạt hơn các khoảng trắng và ký tự đặc biệt xung quanh từ khóa đích.

Bổ sung cơ chế Fallback: Thêm một bước kiểm tra phụ trong mã nguồn: nếu không tìm thấy Action, hệ thống sẽ quét toàn bộ văn bản phản hồi một lần nữa để tìm Final Answer trước khi đưa ra thông báo lỗi Parsing failed.]

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

_Reflect on the reasoning capability difference._

1.  **Reasoning**: So với chatbot truyền thống, khối thought của Agent thực hiện quá trình self-questioning để phân nhỏ các yêu cầu phức tạp của user. 
2.  **Reliability**: Agent tốt hơn chatbot khi giải quyết các tác vụ đòi hỏi dữ liệu thực tế hoặc tính toán logic. Tuy nhiên agent có độ trễ cao hơn chatbot, nếu LLM không tuân thủ cú phá Action:tool_name(args) thì hệ thống Regex sẽ thất bạn
3.  **Observation**: Các Observation đóng vai trò là cơ chế "Grounding" (bám sát thực tế), giúp AI thoát khỏi tình trạng ảo tưởng (hallucination). Phản hồi từ môi trường (ví dụ: kết quả trả về từ công cụ tìm kiếm giáo trình trong search.py) cung cấp kiến thức thực tế để Agent điều chỉnh các bước suy luận tiếp theo. Nếu không có Observation, Agent chỉ là một mô hình ngôn ngữ đóng kín; có Observation, nó trở thành một thực thể có khả năng tương tác và xử lý tác vụ trong thế giới thực.

---

## IV. Future Improvements (5 Points)

_How would you scale this for a production-level AI agent system?_

- **Scalability**: [Kết hợp search_with_llm với một hệ thống RAG (Retrieval-Augmented Generation)để lấy thông tin từ doc/ PDF giáo trình thật thay vì để LLM tự sinh nội dung.]
- **Safety**: [Thêm một lớp kiểm duyệt (Guardrails) để đảm bảo lộ trình học tập do LLM sinh ra tuân thủ đúng chương trình đào tạo của Lab AI.]
- **Performance**: [Áp dụng cơ chế Caching (như Redis) để lưu lại các lộ trình đã sinh ra cho các từ khóa phổ biến, giúp giảm chi phí gọi API và tăng tốc độ phản hồi.]

---

