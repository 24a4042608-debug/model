import { GoogleGenerativeAI } from "@google/generative-ai";
import { generateSlug } from "../utils/vietnamese";

export interface PipelineConfig {
  apiKey: string;
  modelName: string;
  isSimulation: boolean;
  brandName?: string;
}

export interface PipelineStepUpdate {
  id: string;
  label: string;
  status: 'idle' | 'running' | 'success' | 'warning' | 'error';
  message: string;
  output?: any;
  details?: string;
}

export interface SEOResult {
  seo_title: string;
  meta_description: string;
  main_keyword: string;
  secondary_keywords: string[];
  slug: string;
  seo_score: number;
  analysis: {
    title: string;
    description: string;
    ctr: string;
    suggestion: string;
  };
}

// Mock delay helper
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

// Mock simulation generator for demoing without an API Key
const runSimulation = async (
  productName: string,
  _productDescription: string,
  brandName: string = "",
  onStepUpdate: (update: PipelineStepUpdate) => void
): Promise<SEOResult> => {
  // Step 1: Keywords
  onStepUpdate({
    id: "keywords",
    label: "Phân tích từ khóa & USP",
    status: "running",
    message: "Đang phân tích từ khóa chính, phụ và trích xuất USP từ sản phẩm..."
  });
  await delay(1800);

  const mainKeyword = productName.toLowerCase().includes("áo") 
    ? "áo thun nữ ôm body" 
    : (productName.toLowerCase().includes("giày") ? "giày thể thao nam" : productName.toLowerCase().slice(0, 20));
  
  const secondaryKeywords = productName.toLowerCase().includes("áo")
    ? ["áo thun nữ", "áo thun co giãn", "áo body nữ", "áo basic nữ", brandName || "BYJANE 315"]
    : ["giày nam", "giày sneaker", "giày chạy bộ", "giày thể thao", brandName || "SportsPro"];

  const usps = ["Co giãn 4 chiều", "Tôn dáng ôm body", "Thấm hút mồ hôi tốt", "Thiết kế basic dễ phối đồ"];

  onStepUpdate({
    id: "keywords",
    label: "Phân tích từ khóa & USP",
    status: "success",
    message: "Đã trích xuất xong từ khóa và USP.",
    output: { mainKeyword, secondaryKeywords, usps }
  });

  // Step 2: Title Gen & Validation Loop
  onStepUpdate({
    id: "title",
    label: "Sinh SEO Title",
    status: "running",
    message: "Đang sinh tiêu đề SEO tối ưu..."
  });
  await delay(1200);

  let mockTitle = `${brandName ? brandName + ' ' : ''}${mainKeyword.toUpperCase()} - ${usps[0]} ${usps[1]}`;
  // Let's normalize it to sound natural
  mockTitle = productName.toLowerCase().includes("áo")
    ? "Áo Thun Nữ Ôm Body BYJANE 315 Co Giãn Tôn Dáng"
    : `Giày Thể Thao Nam ${brandName} Cực Nhẹ Thoáng Khí`;

  onStepUpdate({
    id: "title",
    label: "Sinh SEO Title",
    status: "warning",
    message: `Kiểm tra độ dài tiêu đề: "${mockTitle}" (${mockTitle.length} ký tự)...`,
    details: `Đang kiểm tra độ dài tiêu đề...\nĐộ dài hiện tại: ${mockTitle.length} ký tự (Chưa đạt chuẩn 50-60 ký tự, giả lập thử lại).`
  });
  await delay(1500);

  // Correcting it to hit the range 50-60 characters
  const correctedTitle = productName.toLowerCase().includes("áo")
    ? "Áo Thun Nữ Ôm Body BYJANE 315 Cao Cấp Co Giãn Tôn Dáng"  // 54 chars
    : `Giày Thể Thao Nam ${brandName || 'Pro'} Cực Nhẹ Co Giãn Êm Chân`; // ~53 chars

  onStepUpdate({
    id: "title",
    label: "Sinh SEO Title",
    status: "success",
    message: `Tiêu đề chuẩn: "${correctedTitle}" (${correctedTitle.length} ký tự). Vượt qua kiểm tra!`,
    output: correctedTitle,
    details: `Vòng lặp tự động sửa lỗi:\n- Lần 1: "${mockTitle}" (${mockTitle.length} ký tự) -> Không đạt.\n- Lần 2: Rút gọn/Bổ sung thêm USP -> "${correctedTitle}" (${correctedTitle.length} ký tự) -> Đạt chuẩn!`
  });

  // Step 3: Meta Description Gen & Validation Loop
  onStepUpdate({
    id: "description",
    label: "Sinh Meta Description",
    status: "running",
    message: "Đang sinh mô tả meta tối ưu..."
  });
  await delay(1500);

  const mockDesc = `${correctedTitle} chất liệu cao cấp, co giãn tốt, mặc cực kỳ thoải mái và tôn dáng. Thích hợp đi làm, đi chơi, dạo phố.`;
  onStepUpdate({
    id: "description",
    label: "Sinh Meta Description",
    status: "warning",
    message: `Kiểm tra độ dài mô tả: ${mockDesc.length} ký tự...`,
    details: `Mô tả hiện tại: "${mockDesc}" (${mockDesc.length} ký tự).\nĐang thiếu CTA (Call-to-Action) hoặc độ dài chưa khớp 140-160 ký tự.`
  });
  await delay(1500);

  const correctedDesc = productName.toLowerCase().includes("áo")
    ? "Áo thun nữ ôm body BYJANE 315 chất thun co giãn mềm mại, tôn dáng, dễ phối đồ. Thiết kế basic phù hợp mặc hằng ngày cực xinh. Mua ngay hôm nay!" // 149 chars
    : `Giày thể thao nam chất liệu siêu nhẹ, thoáng khí, ôm chân êm ái thích hợp chạy bộ và tập gym. Thiết kế cá tính, bền bỉ. Đặt hàng hôm nay nhận ưu đãi!`; // 152 chars

  onStepUpdate({
    id: "description",
    label: "Sinh Meta Description",
    status: "success",
    message: `Mô tả chuẩn: "${correctedDesc}" (${correctedDesc.length} ký tự). Vượt qua kiểm tra!`,
    output: correctedDesc,
    details: `Vòng lặp tự động sửa lỗi:\n- Lần 1: Không có CTA / lệch độ dài.\n- Lần 2: Thêm CTA "Mua ngay..." và tinh chỉnh -> "${correctedDesc}" (${correctedDesc.length} ký tự) -> Đạt chuẩn!`
  });

  // Step 4: Slug & Score
  onStepUpdate({
    id: "scoring",
    label: "Chấm điểm & Xuất JSON",
    status: "running",
    message: "Đang chấm điểm SEO và biên dịch kết quả..."
  });
  await delay(1200);

  const slug = generateSlug(correctedTitle);

  const result: SEOResult = {
    seo_title: correctedTitle,
    meta_description: correctedDesc,
    main_keyword: mainKeyword,
    secondary_keywords: secondaryKeywords,
    slug: slug,
    seo_score: 98,
    analysis: {
      title: "Từ khóa chính ở đầu tiêu đề, độ dài 54 ký tự cực kỳ tối ưu, chứa thương hiệu và USP tôn dáng.",
      description: `Độ dài ${correctedDesc.length} ký tự đạt chuẩn (140-160), chứa từ khóa chính tự nhiên và có CTA kích thích mua hàng.`,
      ctr: "Cao",
      suggestion: "Tiêu đề và mô tả đã rất tốt. Bạn có thể bổ sung thêm màu sắc hoặc size trong slug nếu muốn SEO theo biến thể sản phẩm chi tiết."
    }
  };

  onStepUpdate({
    id: "scoring",
    label: "Chấm điểm & Xuất JSON",
    status: "success",
    message: "Đã hoàn tất tối ưu SEO sản phẩm!",
    output: result
  });

  return result;
};

// Real API pipeline runner
export const runSeoPipeline = async (
  productName: string,
  productDescription: string,
  config: PipelineConfig,
  onStepUpdate: (update: PipelineStepUpdate) => void
): Promise<SEOResult> => {
  const brandName = config.brandName || "";
  
  if (config.isSimulation || !config.apiKey) {
    return runSimulation(productName, productDescription, brandName, onStepUpdate);
  }

  try {
    const genAI = new GoogleGenerativeAI(config.apiKey);
    const model = genAI.getGenerativeModel({
      model: config.modelName || "gemini-2.5-flash",
      generationConfig: {
        responseMimeType: "application/json",
      }
    });

    // ==========================================
    // STEP 1: KEYWORD & USP EXTRACTION
    // ==========================================
    onStepUpdate({
      id: "keywords",
      label: "Phân tích từ khóa & USP",
      status: "running",
      message: "Đang gửi sản phẩm cho AI phân tích từ khóa chính, phụ và các USP..."
    });

    const step1Prompt = `
      Bạn là chuyên gia SEO Ecommerce. Phân tích sản phẩm sau đây:
      Tên sản phẩm: ${productName}
      Mô tả: ${productDescription}
      Thương hiệu (nếu có): ${brandName}

      Nhiệm vụ:
      1. Xác định 1 từ khóa chính (main_keyword) tối ưu nhất, viết thường, có dấu tiếng Việt, thường là tên loại sản phẩm kèm tính chất đặc trưng (ví dụ: "áo thun nữ ôm body", "kem chống nắng nâng tông").
      2. Đề xuất 5 từ khóa phụ (secondary_keywords) liên quan chặt chẽ.
      3. Trích xuất 2-4 USP (Unique Selling Points - ưu điểm nổi bật như co giãn, siêu nhẹ, chống nước, cotton 100%...) của sản phẩm.

      Chỉ trả về JSON có cấu trúc sau:
      {
        "main_keyword": "từ khóa chính",
        "secondary_keywords": ["từ phụ 1", "từ phụ 2", "từ phụ 3", "từ phụ 4", "từ phụ 5"],
        "usps": ["USP 1", "USP 2", "USP 3"]
      }
    `;

    const step1Result = await model.generateContent(step1Prompt);
    const step1Text = step1Result.response.text();
    const step1Json = JSON.parse(step1Text);
    const { main_keyword: mainKeyword, secondary_keywords: secondaryKeywords, usps } = step1Json;

    onStepUpdate({
      id: "keywords",
      label: "Phân tích từ khóa & USP",
      status: "success",
      message: `Đã xác định từ khóa chính: "${mainKeyword}"`,
      output: { mainKeyword, secondaryKeywords, usps }
    });

    // ==========================================
    // STEP 2: SEO TITLE GENERATION & SELF-CORRECTION LOOP
    // ==========================================
    onStepUpdate({
      id: "title",
      label: "Sinh SEO Title",
      status: "running",
      message: "Đang thiết kế tiêu đề SEO bắt đầu bằng từ khóa chính..."
    });

    let titlePrompt = `
      Nhiệm vụ: Tạo 1 tiêu đề SEO Title hoàn hảo cho sản phẩm.
      Tên sản phẩm gốc: ${productName}
      Thương hiệu: ${brandName}
      Từ khóa chính: ${mainKeyword}
      USP nổi bật: ${usps.join(", ")}

      Yêu cầu bắt buộc:
      1. Độ dài tiêu đề: BẮT BUỘC nằm trong khoảng từ 50 đến 60 ký tự.
      2. Từ khóa chính "${mainKeyword}" PHẢI NẰM ĐẦU tiêu đề.
      3. Chứa thương hiệu "${brandName}" nếu có.
      4. Chứa 1-2 USP nổi bật.
      5. Hấp dẫn, tăng CTR, không dùng ký tự spam như ★★★, !!!, >>>.

      Chỉ trả về JSON có cấu trúc:
      {
        "title": "Nội dung tiêu đề SEO"
      }
    `;

    let title = "";
    let titleAttempts = 0;
    let titleLogs = "";
    let titlePassed = false;

    while (titleAttempts < 3 && !titlePassed) {
      titleAttempts++;
      const titleResult = await model.generateContent(titlePrompt);
      const titleJson = JSON.parse(titleResult.response.text());
      title = titleJson.title.trim();
      const titleLen = title.length;

      titleLogs += `Lần ${titleAttempts}: "${title}" (${titleLen} ký tự) -> `;

      if (titleLen >= 50 && titleLen <= 60) {
        titlePassed = true;
        titleLogs += "ĐẠT CHUẨN!\n";
      } else {
        titleLogs += `KHÔNG ĐẠT (Cần 50-60 ký tự).\n`;
        onStepUpdate({
          id: "title",
          label: "Sinh SEO Title",
          status: "warning",
          message: `Tiêu đề "${title}" có độ dài ${titleLen} ký tự. Đang tối ưu lại...`,
          details: titleLogs
        });
        
        // Refine the prompt for correction
        titlePrompt = `
          Tiêu đề bạn đã tạo ở lượt trước là: "${title}" (${titleLen} ký tự).
          Tiêu đề này KHÔNG đạt độ dài chuẩn 50-60 ký tự.
          Vui lòng viết lại tiêu đề này sao cho độ dài BẮT BUỘC phải nằm trong khoảng từ 50 đến 60 ký tự (không thừa, không thiếu).
          
          Giữ nguyên các quy tắc:
          - Bắt đầu bằng từ khóa chính: "${mainKeyword}"
          - Chứa thương hiệu: "${brandName}"
          - Chứa 1-2 USP nổi bật.
          - Không chứa các ký tự spam.
          
          Chỉ trả về JSON:
          {
            "title": "Tiêu đề SEO mới đạt chuẩn"
          }
        `;
      }
    }

    onStepUpdate({
      id: "title",
      label: "Sinh SEO Title",
      status: titlePassed ? "success" : "warning",
      message: titlePassed 
        ? `Tiêu đề chuẩn: "${title}" (${title.length} ký tự).`
        : `Không thể tối ưu chính xác 50-60 ký tự sau 3 lần thử. Sử dụng: "${title}" (${title.length} ký tự)`,
      output: title,
      details: titleLogs
    });

    // ==========================================
    // STEP 3: META DESCRIPTION GENERATION & SELF-CORRECTION LOOP
    // ==========================================
    onStepUpdate({
      id: "description",
      label: "Sinh Meta Description",
      status: "running",
      message: "Đang sinh mô tả meta chứa từ khóa chính và CTA..."
    });

    let descPrompt = `
      Nhiệm vụ: Tạo 1 đoạn mô tả Meta Description hấp dẫn.
      Tên sản phẩm: ${productName}
      Tiêu đề SEO vừa tạo: ${title}
      Từ khóa chính: ${mainKeyword}
      USP: ${usps.join(", ")}
      Thương hiệu: ${brandName}

      Yêu cầu bắt buộc:
      1. Độ dài: BẮT BUỘC từ 140 đến 160 ký tự.
      2. Chứa từ khóa chính "${mainKeyword}" một cách tự nhiên.
      3. Mô tả đúng sản phẩm, có lợi ích cho khách hàng.
      4. Có lời kêu gọi hành động (CTA) nhẹ ở cuối (như: "Mua ngay!", "Khám phá ngay!", "Đặt hàng hôm nay!").

      Chỉ trả về JSON có cấu trúc:
      {
        "description": "Nội dung mô tả meta"
      }
    `;

    let description = "";
    let descAttempts = 0;
    let descLogs = "";
    let descPassed = false;

    while (descAttempts < 3 && !descPassed) {
      descAttempts++;
      const descResult = await model.generateContent(descPrompt);
      const descJson = JSON.parse(descResult.response.text());
      description = descJson.description.trim();
      const descLen = description.length;

      descLogs += `Lần ${descAttempts}: "${description}" (${descLen} ký tự) -> `;

      if (descLen >= 140 && descLen <= 160) {
        descPassed = true;
        descLogs += "ĐẠT CHUẨN!\n";
      } else {
        descLogs += `KHÔNG ĐẠT (Cần 140-160 ký tự).\n`;
        onStepUpdate({
          id: "description",
          label: "Sinh Meta Description",
          status: "warning",
          message: `Mô tả có độ dài ${descLen} ký tự. Đang tối ưu lại...`,
          details: descLogs
        });

        // Refine prompt for correction
        descPrompt = `
          Mô tả bạn đã tạo ở lượt trước là: "${description}" (${descLen} ký tự).
          Mô tả này KHÔNG đạt độ dài chuẩn 140-160 ký tự.
          Vui lòng viết lại mô tả này sao cho độ dài BẮT BUỘC phải nằm trong khoảng từ 140 đến 160 ký tự.
          
          Giữ nguyên các quy tắc:
          - Chứa từ khóa chính: "${mainKeyword}"
          - Mô tả đúng tính chất và lợi ích sản phẩm.
          - Chứa CTA ở cuối (ví dụ: "Mua ngay!", "Khám phá ngay!").
          
          Chỉ trả về JSON:
          {
            "description": "Mô tả meta mới đạt chuẩn"
          }
        `;
      }
    }

    onStepUpdate({
      id: "description",
      label: "Sinh Meta Description",
      status: descPassed ? "success" : "warning",
      message: descPassed 
        ? `Mô tả chuẩn: "${description}" (${description.length} ký tự).`
        : `Sử dụng mô tả tốt nhất: "${description}" (${description.length} ký tự)`,
      output: description,
      details: descLogs
    });

    // ==========================================
    // STEP 4: SEO SCORING & AUDITING
    // ==========================================
    onStepUpdate({
      id: "scoring",
      label: "Chấm điểm & Xuất JSON",
      status: "running",
      message: "Đang đánh giá chất lượng SEO và lập báo cáo chi tiết..."
    });

    const slug = generateSlug(title);

    const scorePrompt = `
      Bạn là kiểm toán viên SEO Ecommerce. Đánh giá kết quả tối ưu SEO cho sản phẩm:
      Tên gốc: ${productName}
      Title SEO: ${title} (Độ dài: ${title.length} ký tự)
      Meta Description: ${description} (Độ dài: ${description.length} ký tự)
      Từ khóa chính: ${mainKeyword}
      Từ khóa phụ: ${secondaryKeywords.join(", ")}
      Slug: ${slug}

      Nhiệm vụ: Chấm điểm SEO từ 0 đến 100 và đưa ra phân tích chi tiết.
      Tiêu chí chấm điểm:
      - Title bắt đầu bằng từ khóa chính, độ dài 50-60 ký tự. (Tối đa 30 điểm)
      - Description tự nhiên, chứa từ khóa, chứa CTA, độ dài 140-160 ký tự. (Tối đa 30 điểm)
      - Từ khóa chính xác, từ phụ phong phú. (Tối đa 20 điểm)
      - Slug viết thường, không dấu, ngăn cách bằng gạch ngang. (Tối đa 10 điểm)
      - CTR ước tính (dựa trên mức độ thu hút). (Tối đa 10 điểm)

      Chỉ trả về JSON cấu trúc:
      {
        "seo_score": 95,
        "analysis": {
          "title": "Đánh giá chi tiết về Title",
          "description": "Đánh giá chi tiết về Description",
          "ctr": "Cao / Trung bình / Thấp",
          "suggestion": "Đề xuất cụ thể cải thiện thêm (nếu có)"
        }
      }
    `;

    const scoreResult = await model.generateContent(scorePrompt);
    const scoreJson = JSON.parse(scoreResult.response.text());

    const result: SEOResult = {
      seo_title: title,
      meta_description: description,
      main_keyword: mainKeyword,
      secondary_keywords: secondaryKeywords,
      slug: slug,
      seo_score: scoreJson.seo_score || 90,
      analysis: {
        title: scoreJson.analysis.title,
        description: scoreJson.analysis.description,
        ctr: scoreJson.analysis.ctr || "Cao",
        suggestion: scoreJson.analysis.suggestion || "Không có đề xuất thêm."
      }
    };

    onStepUpdate({
      id: "scoring",
      label: "Chấm điểm & Xuất JSON",
      status: "success",
      message: `Đã chấm điểm thành công! Điểm SEO: ${result.seo_score}/100.`,
      output: result
    });

    return result;

  } catch (error: any) {
    console.error("SEO Pipeline Error:", error);
    onStepUpdate({
      id: "scoring",
      label: "Chấm điểm & Xuất JSON",
      status: "error",
      message: `Lỗi thực thi pipeline: ${error.message || error}`
    });
    throw error;
  }
};
