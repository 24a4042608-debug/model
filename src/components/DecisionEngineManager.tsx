import React, { useState, useEffect } from "react";
import { Activity, Plus, RefreshCw, Sparkles, TrendingUp, CheckCircle2, Table, Eye, LineChart } from "lucide-react";

interface DecisionEngineManagerProps {
  apiUrl: string;
  isSimulation: boolean;
}

interface DatasetRecord {
  id?: number;
  product_id: string;
  date: string;
  ctr: number;
  cvr: number;
  cpc: number;
  cpa: number;
  roas: number;
  refund: number;
  gmv: number;
  profit: number;
}

interface RecommendationAction {
  priority: number;
  action: string;
  reason: string;
  expected_profit: string;
  difficulty: string;
}

interface ModelMetadata {
  algorithm: string;
  version: string;
  accuracy: number;
  dataset_size: number;
  trained_at?: string;
}

export const DecisionEngineManager: React.FC<DecisionEngineManagerProps> = ({ apiUrl, isSimulation }) => {
  // Navigation states
  const [activeSubTab, setActiveSubTab] = useState<"dashboard" | "history" | "evaluation" | "prediction">("dashboard");

  // Edit & Delete states
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingRecord, setEditingRecord] = useState<DatasetRecord | null>(null);
  
  // Edit form states
  const [editProductId, setEditProductId] = useState("");
  const [editDate, setEditDate] = useState("");
  const [editCtr, setEditCtr] = useState<number>(0);
  const [editCvr, setEditCvr] = useState<number>(0);
  const [editCpc, setEditCpc] = useState<number>(0);
  const [editCpa, setEditCpa] = useState<number>(0);
  const [editRefund, setEditRefund] = useState<number>(0);
  const [editGmv, setEditGmv] = useState<number>(0);
  const [editProfit, setEditProfit] = useState<number>(0);
  const [editRoas, setEditRoas] = useState<number>(0);

  const handleDeleteRecord = async (id: number) => {
    if (!window.confirm("Bạn có chắc chắn muốn xóa bản ghi này?")) return;
    
    if (isSimulation) {
      setDataset(prev => prev.filter(r => r.id !== id));
      alert("Đã xóa bản ghi giả lập thành công!");
      return;
    }
    
    try {
      const res = await fetch(`${apiUrl}/api/decision-engine/dataset/${id}`, {
        method: "DELETE"
      });
      if (res.ok) {
        alert("Xóa bản ghi thành công!");
        fetchCampaignDataset();
      } else {
        alert("Xóa bản ghi thất bại.");
      }
    } catch (e) {
      console.error(e);
      alert("Lỗi kết nối tới Server API.");
    }
  };

  const handleOpenEditModal = (record: DatasetRecord) => {
    setEditingRecord(record);
    setEditProductId(record.product_id);
    setEditDate(record.date);
    setEditCtr(record.ctr);
    setEditCvr(record.cvr);
    setEditCpc(record.cpc);
    setEditCpa(record.cpa);
    setEditRefund(record.refund);
    setEditGmv(record.gmv);
    setEditProfit(record.profit);
    setEditRoas(record.roas);
    setShowEditModal(true);
  };

  const handleUpdateRecordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingRecord || editingRecord.id === undefined) return;
    
    const record: DatasetRecord = {
      id: editingRecord.id,
      product_id: editProductId,
      date: editDate,
      ctr: Number(editCtr),
      cvr: Number(editCvr),
      cpc: Number(editCpc),
      cpa: Number(editCpa),
      roas: Number(editRoas),
      refund: Number(editRefund),
      gmv: Number(editGmv),
      profit: Number(editProfit)
    };
    
    if (isSimulation) {
      setDataset(prev => prev.map(r => r.id === editingRecord.id ? record : r));
      setShowEditModal(false);
      alert("Đã cập nhật bản ghi giả lập thành công!");
      return;
    }
    
    try {
      const res = await fetch(`${apiUrl}/api/decision-engine/dataset/${editingRecord.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(record)
      });
      if (res.ok) {
        alert("Cập nhật bản ghi thành công!");
        setShowEditModal(false);
        fetchCampaignDataset();
      } else {
        alert("Cập nhật bản ghi thất bại.");
      }
    } catch (e) {
      console.error(e);
      alert("Lỗi kết nối tới Server API.");
    }
  };

  // Model Registry State
  const [modelMeta, setModelMeta] = useState<ModelMetadata | null>(null);
  const [isTraining, setIsTraining] = useState(false);
  const [selectedAlgo, setSelectedAlgo] = useState("XGBoost");

  // Dataset State
  const [dataset, setDataset] = useState<DatasetRecord[]>([]);
  const [isFetchingData, setIsFetchingData] = useState(false);

  // Evaluation State
  const [evalList, setEvalList] = useState<any[]>([]);
  const [evalMetrics, setEvalMetrics] = useState<any>(null);
  const [isEvaluating, setIsEvaluating] = useState(false);

  // Input states for Training Data Seed
  const [trainDate, setTrainDate] = useState(() => new Date().toISOString().split("T")[0]);
  const [trainProductId, setTrainProductId] = useState("byjane_cardigan_945");
  const [impressions, setImpressions] = useState<number | "">(9035);
  const [clicks, setClicks] = useState<number | "">(256);
  const [conversions, setConversions] = useState<number | "">(10);
  const [orders, setOrders] = useState<number | "">(13);
  const [gmv, setGmv] = useState<number | "">(2452000);
  const [cost, setCost] = useState<number | "">(116445);
  const [refundRate, setRefundRate] = useState<number>(1.5);
  const [isImporting, setIsImporting] = useState(false);

  // States for Prediction & Recommendations
  const [currCtr, setCurrCtr] = useState<number>(2.83);
  const [currCvr, setCurrCvr] = useState<number>(3.9);
  const [currCpa, setCurrCpa] = useState<number>(11645);
  const [currRefund, setCurrRefund] = useState<number>(1.5);
  const [targetRoas, setTargetRoas] = useState<number>(4.5);
  const [targetProfit, setTargetProfit] = useState<number>(5000000);

  const [recommendations, setRecommendations] = useState<RecommendationAction[]>([]);
  const [optimizedResults, setOptimizedResults] = useState<any>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);

  // Fetch model metadata
  const fetchModelMeta = async () => {
    if (isSimulation) {
      setModelMeta({
        algorithm: "XGBoost (Simulation)",
        version: "v1.0.0",
        accuracy: 0.88,
        dataset_size: 100,
        trained_at: new Date().toLocaleString("vi-VN"),
      });
      return;
    }
    try {
      const res = await fetch(`${apiUrl}/api/decision-engine/train/registry`);
      if (res.ok) {
        const data = await res.json();
        if (data.algorithm) {
          setModelMeta(data);
        }
      }
    } catch (e) {
      console.error("Error fetching model registry:", e);
    }
  };

  // Fetch Campaign Dataset
  const fetchCampaignDataset = async () => {
    setIsFetchingData(true);
    if (isSimulation) {
      setTimeout(() => {
        const mock: DatasetRecord[] = [];
        const today = new Date();
        const products = [
          { id: "ao_thun_local_brand_unisex", price: 185000, refund: 2.5 },
          { id: "son_kem_li_matte_blackrouge", price: 160000, refund: 1.2 },
          { id: "kem_chong_nang_la_roche_posay", price: 380000, refund: 0.8 },
          { id: "vay_hoa_nhi_vintage_dang_xoe", price: 270000, refund: 4.0 }
        ];
        
        for (let i = 100; i > 0; i--) {
          const d = new Date(today);
          d.setDate(today.getDate() - i);
          
          const prod = products[Math.floor(Math.random() * products.length)];
          const isWeekend = d.getDay() === 0 || d.getDay() === 5 || d.getDay() === 6; // Fri, Sat, Sun
          const isDoubleDay = [1, 2, 5, 6, 7, 8, 9, 10, 11, 12, 15, 25].includes(d.getDate());
          
          let baseBudget = 250000 + Math.random() * 950000;
          if (isDoubleDay) baseBudget *= 2.5;
          else if (isWeekend) baseBudget *= 1.25;
          
          const budget = Math.floor(baseBudget);
          
          let baseCpc = 450 + Math.random() * 500;
          if (isDoubleDay) baseCpc *= 1.2;
          const cpc = parseFloat(baseCpc.toFixed(2));
          
          let clicks = Math.floor(budget / cpc);
          if (clicks === 0) clicks = 1;
          
          let baseCtr = 1.8 + Math.random() * 2.0;
          if (isDoubleDay) baseCtr += 0.8;
          else if (isWeekend) baseCtr += 0.3;
          const ctr = parseFloat(baseCtr.toFixed(2));
          
          let baseCvr = 2.2 + Math.random() * 2.6;
          if (isDoubleDay) baseCvr += 1.8;
          else if (isWeekend) baseCvr += 0.5;
          const cvr = parseFloat(baseCvr.toFixed(2));
          
          let conversions = Math.floor(clicks * (cvr / 100));
          if (conversions === 0) conversions = Math.floor(1 + Math.random() * 2);
          
          const cost = clicks * cpc;
          const gmv = conversions * prod.price;
          const cpa = parseFloat((cost / conversions).toFixed(2));
          const roas = parseFloat((gmv / cost).toFixed(2));
          const refund = parseFloat((prod.refund + (Math.random() * 1.0 - 0.5)).toFixed(2));
          const profit = parseFloat((gmv * 0.45 - cost - (gmv * (refund / 100))).toFixed(2));
          
          mock.push({
            id: i,
            product_id: prod.id,
            date: d.toISOString().split("T")[0],
            ctr,
            cvr,
            cpc,
            cpa: Math.round(cpa),
            roas,
            refund: Math.max(0.1, refund),
            gmv,
            profit
          });
        }
        setDataset(mock);
        setCurrentPage(1);
        setIsFetchingData(false);
      }, 800);
      return;
    }
    try {
      const res = await fetch(`${apiUrl}/api/decision-engine/dataset`);
      if (res.ok) {
        const data = await res.json();
        setDataset(data);
        setCurrentPage(1);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsFetchingData(false);
    }
  };

  // Fetch Evaluation Data
  const runModelEvaluation = async () => {
    setIsEvaluating(true);
    if (isSimulation) {
      setTimeout(() => {
        const today = new Date();
        const mockEvals = [];
        for (let i = 10; i > 0; i--) {
          const d = new Date(today);
          d.setDate(today.getDate() - i);
          const act = parseFloat((12.0 + Math.random() * 8).toFixed(2));
          const dev = parseFloat((Math.random() * 1.5 - 0.75).toFixed(2));
          mockEvals.push({
            date: d.toISOString().split("T")[0],
            actual_roas: act,
            predicted_roas: parseFloat((act + dev).toFixed(2)),
            actual_gmv: 2500000,
            predicted_gmv: 2550000,
            actual_profit: 650000,
            predicted_profit: 660000,
            error_pct: parseFloat((Math.abs(dev) / act * 100).toFixed(1))
          });
        }
        setEvalList(mockEvals);
        setEvalMetrics({ mae_roas: 0.65, sample_size: 10 });
        setIsEvaluating(false);
      }, 1000);
      return;
    }
    try {
      const res = await fetch(`${apiUrl}/api/decision-engine/evaluate`);
      if (res.ok) {
        const data = await res.json();
        setEvalList(data.evaluations || []);
        setEvalMetrics(data.metrics || null);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsEvaluating(false);
    }
  };

  useEffect(() => {
    fetchModelMeta();
    fetchCampaignDataset();
  }, [apiUrl, isSimulation]);

  // Handle Model Training
  const handleTrainModel = async () => {
    setIsTraining(true);
    try {
      if (isSimulation) {
        setTimeout(() => {
          setModelMeta({
            algorithm: `${selectedAlgo} (Simulation)`,
            version: "v" + (1 + Math.random()).toFixed(2),
            accuracy: 0.85 + Math.random() * 0.1,
            dataset_size: dataset.length || 100,
            trained_at: new Date().toLocaleString("vi-VN"),
          });
          setIsTraining(false);
          alert("Huấn luyện mô hình giả lập thành công!");
        }, 1500);
        return;
      }

      const res = await fetch(`${apiUrl}/api/decision-engine/train`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ algorithm: selectedAlgo }),
      });

      if (res.ok) {
        const data = await res.json();
        alert(`Huấn luyện mô hình thành công! Thuật toán: ${data.metadata.algorithm}, R² Accuracy: ${(data.metadata.accuracy * 100).toFixed(1)}%`);
        fetchModelMeta();
        fetchCampaignDataset();
      } else {
        alert("Huấn luyện mô hình thất bại.");
      }
    } catch (e) {
      console.error(e);
      alert("Lỗi kết nối tới Server API.");
    } finally {
      setIsTraining(false);
    }
  };

  // Import Campaign Data
  const handleImportAndTrain = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!clicks || !impressions || !conversions || !gmv || !cost) {
      alert("Vui lòng điền đầy đủ các chỉ số hiệu suất quảng cáo.");
      return;
    }

    setIsImporting(true);

    const calculatedCtr = parseFloat(((Number(clicks) / Number(impressions)) * 100).toFixed(2));
    const calculatedCvr = parseFloat(((Number(conversions) / Number(clicks)) * 100).toFixed(2));
    const calculatedCpc = parseFloat((Number(cost) / Number(clicks)).toFixed(2));
    const calculatedCpa = parseFloat((Number(cost) / Number(conversions)).toFixed(2));
    const calculatedRoas = parseFloat((Number(gmv) / Number(cost)).toFixed(2));
    const calculatedProfit = parseFloat((Number(gmv) * 0.35 - Number(cost) - (Number(gmv) * (refundRate / 100))).toFixed(2));

    const record: DatasetRecord = {
      product_id: trainProductId,
      date: trainDate,
      ctr: calculatedCtr,
      cvr: calculatedCvr,
      cpc: calculatedCpc,
      cpa: calculatedCpa,
      roas: calculatedRoas,
      refund: refundRate,
      gmv: Number(gmv),
      profit: calculatedProfit
    };

    try {
      if (isSimulation) {
        setTimeout(async () => {
          alert(`[Simulation] Đã thêm chỉ số vào tập dữ liệu!\n- CTR: ${calculatedCtr}%\n- CVR: ${calculatedCvr}%\n- ROAS: ${calculatedRoas}`);
          setDataset(prev => [record, ...prev]);
          setIsImporting(false);
          setShowAddModal(false);
          handleTrainModel();
        }, 1000);
        return;
      }

      const importRes = await fetch(`${apiUrl}/api/decision-engine/dataset/import`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ records: [record] }),
      });

      if (importRes.ok) {
        const trainRes = await fetch(`${apiUrl}/api/decision-engine/train`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ algorithm: selectedAlgo }),
        });

        if (trainRes.ok) {
          alert("Đã lưu chỉ số quảng cáo vào cơ sở dữ liệu và tự động huấn luyện lại mô hình thành công!");
          fetchModelMeta();
          fetchCampaignDataset();
          setShowAddModal(false);
        } else {
          alert("Đã thêm dữ liệu quảng cáo nhưng tự động huấn luyện lại mô hình gặp lỗi.");
          setShowAddModal(false);
        }
      } else {
        const err = await importRes.json();
        alert("Lỗi lưu dữ liệu: " + (err.detail?.message || "Không xác định"));
      }
    } catch (e) {
      console.error(e);
      alert("Lỗi kết nối tới Server API.");
    } finally {
      setIsImporting(false);
    }
  };

  // Run Optimizer Recommendations
  const handleGetRecommendations = async () => {
    setIsAnalyzing(true);
    try {
      if (isSimulation) {
        setTimeout(() => {
          setRecommendations([
            {
              priority: 1,
              action: `Tăng CTR lên ${Math.min(6.0, currCtr + 0.8).toFixed(2)}%`,
              reason: `Tỷ lệ CTR hiện tại (${currCtr}%) đang thấp hơn mức hiệu suất trung bình tối ưu. CTR tác động trực tiếp đến lưu lượng truy cập và tổng doanh số bán hàng.`,
              expected_profit: "+18.5%",
              difficulty: "Low"
            },
            {
              priority: 2,
              action: "Tối ưu hóa CPA mục tiêu xuống dưới 9,500đ",
              reason: `Mức CPA hiện tại (${currCpa.toLocaleString("vi-VN")}đ) đang bào mòn biên lợi nhuận của sản phẩm. Bạn nên điều chỉnh giá thầu tìm kiếm thông minh hơn.`,
              expected_profit: "+14.2%",
              difficulty: "Medium"
            }
          ]);
          setOptimizedResults({
            optimized_inputs: {
              ctr: Math.min(6.0, currCtr + 0.8).toFixed(2),
              cvr: Math.min(12.0, currCvr + 1.2).toFixed(2),
              cpa: 9200,
              refund: currRefund
            },
            optimized_predictions: {
              roas: (targetRoas + 1.2 + Math.random() * 0.5).toFixed(2),
              profit: targetProfit + 850000,
              gmv: 12500000,
              confidence: 91
            }
          });
          setIsAnalyzing(false);
        }, 1200);
        return;
      }

      const payload = {
        target_profit: targetProfit,
        target_roas: targetRoas,
        max_refund: 3.0,
        current_inputs: {
          ctr: currCtr,
          cvr: currCvr,
          cpa: currCpa,
          refund: currRefund
        }
      };

      const res = await fetch(`${apiUrl}/api/decision-engine/recommend`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        const data = await res.json();
        setRecommendations(data.actions || []);
        setOptimizedResults({
          optimized_inputs: data.rules_evaluated,
          optimized_predictions: data.current_predictions
        });
      } else {
        alert("Không thể tính toán tối ưu gợi ý.");
      }
    } catch (e) {
      console.error(e);
      alert("Lỗi kết nối tới Server API.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="manager-section flex flex-col gap-6">
      
      {/* Premium Sub-Tab Switcher */}
      <div className="subtabs-list">
        <button
          onClick={() => setActiveSubTab("dashboard")}
          className={`subtab-item ${activeSubTab === "dashboard" ? "active" : ""}`}
        >
          <LineChart size={14} />
          <span>Dashboard ROAS</span>
        </button>

        <button
          onClick={() => setActiveSubTab("history")}
          className={`subtab-item ${activeSubTab === "history" ? "active" : ""}`}
        >
          <Table size={14} />
          <span>Bảng Dữ liệu & Nhập liệu ({dataset.length})</span>
        </button>

        <button
          onClick={() => {
            setActiveSubTab("evaluation");
            runModelEvaluation();
          }}
          className={`subtab-item ${activeSubTab === "evaluation" ? "active" : ""}`}
        >
          <Eye size={14} />
          <span>Đánh giá Mô hình trên Tập Data ({evalList.length})</span>
        </button>

        <button
          onClick={() => setActiveSubTab("prediction")}
          className={`subtab-item ${activeSubTab === "prediction" ? "active" : ""}`}
        >
          <Sparkles size={14} />
          <span>Mô phỏng & Dự đoán ROAS riêng</span>
        </button>
      </div>

      {/* ----------------- SUB-TAB 0: ROAS DASHBOARD ----------------- */}
      {activeSubTab === "dashboard" && (
        <div className="flex flex-col gap-6 animate-enter">
          {/* Top Level Metric Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="stats-card-light flex items-center justify-between p-4 bg-zinc-900/60 border border-zinc-800 rounded-lg">
              <div className="flex flex-col gap-1">
                <span className="text-xxs font-bold text-zinc-500 uppercase tracking-wider">Tổng Lợi Nhuận Ròng</span>
                <span className={`text-lg font-bold ${dataset.reduce((sum, r) => sum + r.profit, 0) >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                  {Math.round(dataset.reduce((sum, r) => sum + r.profit, 0)).toLocaleString("vi-VN")}đ
                </span>
              </div>
              <div className="p-2 bg-emerald-500/10 rounded-md text-emerald-400">
                <TrendingUp size={20} />
              </div>
            </div>

            <div className="stats-card-light flex items-center justify-between p-4 bg-zinc-900/60 border border-zinc-800 rounded-lg">
              <div className="flex flex-col gap-1">
                <span className="text-xxs font-bold text-zinc-500 uppercase tracking-wider">Doanh thu GMV</span>
                <span className="text-lg font-bold text-zinc-200">
                  {Math.round(dataset.reduce((sum, r) => sum + r.gmv, 0)).toLocaleString("vi-VN")}đ
                </span>
              </div>
              <div className="p-2 bg-sky-500/10 rounded-md text-sky-400">
                <Activity size={20} />
              </div>
            </div>

            <div className="stats-card-light flex items-center justify-between p-4 bg-zinc-900/60 border border-zinc-800 rounded-lg">
              <div className="flex flex-col gap-1">
                <span className="text-xxs font-bold text-zinc-500 uppercase tracking-wider">Chi Phí Quảng Cáo</span>
                <span className="text-lg font-bold text-zinc-200">
                  {Math.round(dataset.reduce((sum, r) => sum + (r.roas > 0 ? r.gmv / r.roas : 0), 0)).toLocaleString("vi-VN")}đ
                </span>
              </div>
              <div className="p-2 bg-violet-500/10 rounded-md text-violet-400">
                <Table size={20} />
              </div>
            </div>

            <div className="stats-card-light flex items-center justify-between p-4 bg-zinc-900/60 border border-zinc-800 rounded-lg">
              <div className="flex flex-col gap-1">
                <span className="text-xxs font-bold text-zinc-500 uppercase tracking-wider">ROAS Trung Bình</span>
                <span className="text-lg font-bold text-emerald-400">
                  {(dataset.length > 0 ? dataset.reduce((sum, r) => sum + r.roas, 0) / dataset.length : 0).toFixed(2)}x
                </span>
              </div>
              <div className="p-2 bg-emerald-500/10 rounded-md text-emerald-400">
                <Sparkles size={20} />
              </div>
            </div>
          </div>

          {/* Detailed stats grids */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Top performing campaigns list */}
            <div className="section-card flex flex-col p-5 bg-zinc-900/40 border border-zinc-800/80 rounded-lg md:col-span-2">
              <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-wider mb-4">Top 5 Chiến dịch Ads Sinh Lợi Tốt Nhất</h3>
              <div className="flex flex-col gap-3">
                {(() => {
                  const productSummaryMap: { [pid: string]: { profit: number; gmv: number; roasSum: number; count: number } } = {};
                  dataset.forEach(r => {
                    if (!productSummaryMap[r.product_id]) {
                      productSummaryMap[r.product_id] = { profit: 0, gmv: 0, roasSum: 0, count: 0 };
                    }
                    const entry = productSummaryMap[r.product_id];
                    entry.profit += r.profit;
                    entry.gmv += r.gmv;
                    entry.roasSum += r.roas;
                    entry.count += 1;
                  });
                  
                  const productSummaries = Object.keys(productSummaryMap).map(pid => ({
                    product_id: pid,
                    profit: productSummaryMap[pid].profit,
                    gmv: productSummaryMap[pid].gmv,
                    avgRoas: productSummaryMap[pid].roasSum / productSummaryMap[pid].count,
                  })).sort((a, b) => b.profit - a.profit).slice(0, 5);

                  if (productSummaries.length === 0) {
                    return <p className="text-zinc-500 text-xs py-4 text-center">Chưa có dữ liệu chiến dịch.</p>;
                  }

                  return productSummaries.map((tp, idx) => (
                    <div key={idx} className="flex items-center justify-between p-3 bg-zinc-900/60 border border-zinc-850 rounded-lg hover:border-violet-500/20 transition-all duration-200">
                      <div className="flex items-center gap-3">
                        <div className="w-6 h-6 rounded-full bg-violet-600/10 text-violet-400 font-bold flex items-center justify-center text-xs">
                          {idx + 1}
                        </div>
                        <div className="flex flex-col">
                          <span className="text-xs font-bold text-zinc-300 font-mono">{tp.product_id}</span>
                          <span className="text-[10px] text-zinc-500">GMV: {Math.round(tp.gmv).toLocaleString("vi-VN")}đ | ROAS: {tp.avgRoas.toFixed(2)}x</span>
                        </div>
                      </div>
                      <div className="flex flex-col items-end">
                        <span className="text-xs font-bold text-emerald-400">+{Math.round(tp.profit).toLocaleString("vi-VN")}đ</span>
                        <span className="text-[9px] text-zinc-500 uppercase tracking-wider font-semibold">Lợi nhuận ròng</span>
                      </div>
                    </div>
                  ));
                })()}
              </div>
            </div>

            {/* Performance Breakdown Indicators */}
            <div className="section-card flex flex-col p-5 bg-zinc-900/40 border border-zinc-800/80 rounded-lg">
              <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-wider mb-4">Chỉ số Hiệu suất Vận hành</h3>
              <div className="flex flex-col gap-4">
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xxs text-zinc-400 font-semibold uppercase tracking-wider">Tỉ lệ CTR Trung bình</span>
                    <span className="text-xs font-bold text-zinc-200">
                      {(dataset.length > 0 ? dataset.reduce((sum, r) => sum + r.ctr, 0) / dataset.length : 0).toFixed(2)}%
                    </span>
                  </div>
                  <div className="w-full bg-zinc-800 rounded-full h-1.5">
                    <div 
                      className="bg-sky-500 h-1.5 rounded-full" 
                      style={{ width: `${Math.min(100, (dataset.length > 0 ? dataset.reduce((sum, r) => sum + r.ctr, 0) / dataset.length : 0) * 15)}%` }}
                    ></div>
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xxs text-zinc-400 font-semibold uppercase tracking-wider">Tỉ lệ CVR Trung bình</span>
                    <span className="text-xs font-bold text-zinc-200">
                      {(dataset.length > 0 ? dataset.reduce((sum, r) => sum + r.cvr, 0) / dataset.length : 0).toFixed(2)}%
                    </span>
                  </div>
                  <div className="w-full bg-zinc-800 rounded-full h-1.5">
                    <div 
                      className="bg-violet-500 h-1.5 rounded-full" 
                      style={{ width: `${Math.min(100, (dataset.length > 0 ? dataset.reduce((sum, r) => sum + r.cvr, 0) / dataset.length : 0) * 10)}%` }}
                    ></div>
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xxs text-zinc-400 font-semibold uppercase tracking-wider">Tỉ lệ Hoàn Hàng Trung bình</span>
                    <span className="text-xs font-bold text-red-400">
                      {(dataset.length > 0 ? dataset.reduce((sum, r) => sum + r.refund, 0) / dataset.length : 0).toFixed(2)}%
                    </span>
                  </div>
                  <div className="w-full bg-zinc-800 rounded-full h-1.5">
                    <div 
                      className="bg-red-500/80 h-1.5 rounded-full" 
                      style={{ width: `${Math.min(100, (dataset.length > 0 ? dataset.reduce((sum, r) => sum + r.refund, 0) / dataset.length : 0) * 20)}%` }}
                    ></div>
                  </div>
                </div>

                <div className="mt-4 pt-4 border-t border-zinc-800/80">
                  <div className="flex items-center gap-2 text-xxs text-zinc-500 font-semibold uppercase tracking-wider mb-2">
                    <Sparkles size={12} className="text-violet-400" />
                    <span>Trạng thái Model Registry</span>
                  </div>
                  <div className="p-3 bg-zinc-900/60 border border-zinc-850 rounded-lg flex flex-col gap-1">
                    <div className="flex justify-between text-xs text-zinc-300">
                      <span>Thuật toán:</span>
                      <span className="font-bold text-violet-400">{modelMeta?.algorithm || "Chưa huấn luyện"}</span>
                    </div>
                    <div className="flex justify-between text-xs text-zinc-300">
                      <span>R² Accuracy:</span>
                      <span className="font-bold text-emerald-400">
                        {modelMeta?.accuracy ? `${(modelMeta.accuracy * 100).toFixed(1)}%` : "N/A"}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ----------------- SUB-TAB 1: DATA HISTORY & INPUT ----------------- */}
      {activeSubTab === "history" && (
        <div className="flex flex-col gap-6 animate-enter">
          {/* Main Full-width Data Table */}
          <div className="section-card input-panel-card flex flex-col w-full">
            <div className="panel-header justify-between flex-wrap gap-3">
              <div className="flex items-center gap-2">
                <Table size={18} className="header-icon text-emerald-400" />
                <h2>Dữ liệu Lịch sử Chiến dịch ({dataset.length} ngày)</h2>
              </div>
              <div className="flex items-center gap-2">
                <button 
                  onClick={() => setShowAddModal(true)}
                  className="btn-primary py-1.5 px-3 text-xxs flex items-center gap-1.5 bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-700 hover:to-indigo-700 font-bold"
                  style={{ borderRadius: "6px" }}
                >
                  <Plus size={12} />
                  <span>Nhập chỉ số chiến dịch</span>
                </button>
                <button 
                  onClick={fetchCampaignDataset}
                  disabled={isFetchingData}
                  className="btn-secondary py-1 px-3 text-xxs flex items-center gap-1 border border-zinc-800 hover:bg-zinc-800"
                >
                  <RefreshCw size={10} className={isFetchingData ? "animate-spin" : ""} />
                  <span>Làm mới</span>
                </button>
              </div>
            </div>

            <div className="p-0 overflow-x-auto">
              <table className="products-table">
                <thead>
                  <tr>
                    <th>Ngày</th>
                    <th>CTR %</th>
                    <th>CVR %</th>
                    <th>CPA (đ)</th>
                    <th>CPC (đ)</th>
                    <th>ROAS</th>
                    <th>Doanh thu GMV</th>
                    <th>Lợi nhuận</th>
                    <th>Hành động</th>
                  </tr>
                </thead>
                <tbody>
                  {isFetchingData ? (
                    <tr>
                      <td colSpan={9} className="text-center py-12 text-zinc-500 text-xs">
                        Đang tải tập dữ liệu thô từ cơ sở dữ liệu...
                      </td>
                    </tr>
                  ) : dataset.length === 0 ? (
                    <tr>
                      <td colSpan={9} className="text-center py-12 text-zinc-500 text-xs">
                        Chưa có dữ liệu huấn luyện. Hãy nhấn nút Nhập chỉ số để thêm bản ghi đầu tiên.
                      </td>
                    </tr>
                  ) : (
                    dataset.slice((currentPage - 1) * 10, currentPage * 10).map((row, idx) => (
                      <tr key={idx} className="hover:bg-zinc-900/40">
                        <td className="font-mono text-xxs font-bold text-violet-400 whitespace-nowrap">{row.date}</td>
                        <td className="text-zinc-200 text-xs">{row.ctr}%</td>
                        <td className="text-zinc-200 text-xs">{row.cvr}%</td>
                        <td className="text-zinc-200 text-xs">{Math.round(row.cpa).toLocaleString("vi-VN")}đ</td>
                        <td className="text-zinc-400 text-xs">{Math.round(row.cpc).toLocaleString("vi-VN")}đ</td>
                        <td className="text-emerald-400 font-bold text-xs">{row.roas}x</td>
                        <td className="text-zinc-200 text-xs">{Math.round(row.gmv).toLocaleString("vi-VN")}đ</td>
                        <td className={`text-xs font-semibold ${row.profit >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                          {Math.round(row.profit).toLocaleString("vi-VN")}đ
                        </td>
                        <td className="text-xs">
                          <div className="flex items-center gap-2">
                            <button 
                              onClick={() => handleOpenEditModal(row)}
                              className="text-violet-400 hover:text-violet-300 font-semibold"
                            >
                              Sửa
                            </button>
                            <button 
                              onClick={() => row.id !== undefined && handleDeleteRecord(row.id)}
                              className="text-red-400 hover:text-red-300 font-semibold text-stroke-none bg-transparent border-none cursor-pointer"
                            >
                              Xóa
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls */}
            {dataset.length > 0 && (
              <div className="flex items-center justify-between border-t border-zinc-800/80 pt-4 mt-2">
                <span className="text-xxs text-zinc-500">
                  Hiển thị bản ghi {((currentPage - 1) * 10) + 1} - {Math.min(currentPage * 10, dataset.length)} trên tổng số {dataset.length} ngày
                </span>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                    disabled={currentPage === 1 || isFetchingData}
                    className="btn-secondary py-1 px-3 text-xxs disabled:opacity-40 border border-zinc-800 hover:bg-zinc-800 cursor-pointer"
                    style={{ borderRadius: "4px" }}
                  >
                    Trước
                  </button>
                  <span className="text-xs text-zinc-400 font-bold px-2">
                    Trang {currentPage} / {Math.ceil(dataset.length / 10)}
                  </span>
                  <button
                    onClick={() => setCurrentPage(p => Math.min(Math.ceil(dataset.length / 10), p + 1))}
                    disabled={currentPage === Math.ceil(dataset.length / 10) || isFetchingData}
                    className="btn-secondary py-1 px-3 text-xxs disabled:opacity-40 border border-zinc-800 hover:bg-zinc-800 cursor-pointer"
                    style={{ borderRadius: "4px" }}
                  >
                    Sau
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Campaign Index Entry Popup Modal */}
          {showAddModal && (
            <div className="modal-backdrop">
              <div className="modal-container max-w-lg">
                <div className="modal-header">
                  <h3>Nhập chỉ số Chiến dịch</h3>
                  <button 
                    onClick={() => setShowAddModal(false)}
                    className="text-zinc-500 hover:text-zinc-300 font-bold"
                  >
                    ✕
                  </button>
                </div>
                <form onSubmit={handleImportAndTrain} className="modal-form">
                  <div className="grid grid-cols-2 gap-3">
                    <div className="flex flex-col gap-1">
                      <label className="text-xs font-semibold text-zinc-400">ID sản phẩm chạy ADS</label>
                      <input
                        type="text"
                        value={trainProductId}
                        onChange={(e) => setTrainProductId(e.target.value)}
                        className="form-input text-xs"
                        required
                      />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-xs font-semibold text-zinc-400">Ngày thống kê</label>
                      <input
                        type="date"
                        value={trainDate}
                        onChange={(e) => setTrainDate(e.target.value)}
                        className="form-input text-xs"
                        required
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div className="flex flex-col gap-1">
                      <label className="text-xs font-semibold text-zinc-400">Lượt xem (Imp)</label>
                      <input
                        type="number"
                        min="1"
                        value={impressions}
                        onChange={(e) => setImpressions(e.target.value === "" ? "" : Number(e.target.value))}
                        className="form-input text-xs"
                        required
                      />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-xs font-semibold text-zinc-400">Số lượt click</label>
                      <input
                        type="number"
                        min="0"
                        value={clicks}
                        onChange={(e) => setClicks(e.target.value === "" ? "" : Number(e.target.value))}
                        className="form-input text-xs"
                        required
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div className="flex flex-col gap-1">
                      <label className="text-xs font-semibold text-zinc-400">Lượt chuyển đổi</label>
                      <input
                        type="number"
                        min="0"
                        value={conversions}
                        onChange={(e) => setConversions(e.target.value === "" ? "" : Number(e.target.value))}
                        className="form-input text-xs"
                        required
                      />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-xs font-semibold text-zinc-400">Đơn hàng</label>
                      <input
                        type="number"
                        min="0"
                        value={orders}
                        onChange={(e) => setOrders(e.target.value === "" ? "" : Number(e.target.value))}
                        className="form-input text-xs"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div className="flex flex-col gap-1">
                      <label className="text-xs font-semibold text-zinc-400">Doanh thu GMV (đ)</label>
                      <input
                        type="number"
                        min="0"
                        value={gmv}
                        onChange={(e) => setGmv(e.target.value === "" ? "" : Number(e.target.value))}
                        className="form-input text-xs"
                        required
                      />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-xs font-semibold text-zinc-400">Chi phí Ads (đ)</label>
                      <input
                        type="number"
                        min="0"
                        value={cost}
                        onChange={(e) => setCost(e.target.value === "" ? "" : Number(e.target.value))}
                        className="form-input text-xs"
                        required
                      />
                    </div>
                  </div>

                  <div className="flex flex-col gap-1">
                    <label className="text-xs font-semibold text-zinc-400">Tỷ lệ hoàn hàng (%)</label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      step="0.1"
                      value={refundRate}
                      onChange={(e) => setRefundRate(Number(e.target.value))}
                      className="form-input text-xs w-32"
                    />
                  </div>

                  <div className="modal-footer">
                    <button 
                      type="button" 
                      className="btn-secondary" 
                      onClick={() => setShowAddModal(false)}
                    >
                      Hủy
                    </button>
                    <button 
                      type="submit" 
                      className="btn-primary" 
                      disabled={isImporting || isTraining}
                    >
                      {isImporting ? "Đang lưu & Train..." : "Lưu chỉ số & Train"}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ----------------- SUB-TAB 2: AI MODEL EVALUATION ----------------- */}
      {activeSubTab === "evaluation" && (
        <div className="flex flex-col gap-6">
          {/* Model Registry Status Card */}
          <div className="section-card input-panel-card">
            <div className="panel-header justify-between">
              <div className="flex items-center gap-2">
                <TrendingUp size={20} className="header-icon text-violet" />
                <h2>Trạng thái Mô hình Học máy & Cấu hình</h2>
              </div>
              <div className="flex items-center gap-2">
                <select
                  value={selectedAlgo}
                  onChange={(e) => setSelectedAlgo(e.target.value)}
                  className="form-select text-xs py-1 px-2"
                  style={{ height: "auto" }}
                  disabled={isTraining}
                >
                  <option value="XGBoost">XGBoost (Độ chính xác cao)</option>
                  <option value="LightGBM">LightGBM (Nhanh & Tối ưu)</option>
                  <option value="RandomForest">Random Forest (Ổn định)</option>
                  <option value="Ridge">Linear Regression (Tuyến tính)</option>
                </select>
                <button
                  onClick={handleTrainModel}
                  disabled={isTraining}
                  className="btn-primary py-1.5 px-3 text-xs flex items-center gap-1.5"
                  style={{ borderRadius: "6px" }}
                >
                  <RefreshCw size={12} className={isTraining ? "animate-spin" : ""} />
                  <span>{isTraining ? "Đang huấn luyện..." : "Huấn luyện lại"}</span>
                </button>
              </div>
            </div>

            {modelMeta ? (
              <div className="stats-grid-light">
                <div className="stats-card-light">
                  <span className="label">Thuật toán hoạt động</span>
                  <span className="val font-mono text-violet">{modelMeta.algorithm}</span>
                </div>
                <div className="stats-card-light">
                  <span className="label">Độ chính xác (R²)</span>
                  <span className="val text-success">{(modelMeta.accuracy * 100).toFixed(1)}%</span>
                </div>
                <div className="stats-card-light">
                  <span className="label">Kích thước Tập mẫu</span>
                  <span className="val">{modelMeta.dataset_size} ngày vận hành</span>
                </div>
                <div className="stats-card-light">
                  <span className="label">Cập nhật lần cuối</span>
                  <span className="val text-xs text-secondary">{modelMeta.trained_at || "Vừa xong"}</span>
                </div>
              </div>
            ) : (
              <div className="text-center py-4 text-xs text-zinc-500">
                Mô hình dự đoán chưa được khởi tạo.
              </div>
            )}
          </div>

          {/* Test Predictions Comparison */}
          <div className="section-card input-panel-card">
            <div className="panel-header justify-between">
              <div className="flex items-center gap-2">
                <LineChart size={18} className="header-icon text-indigo" />
                <h2>Đánh giá sai số dự đoán: Thực tế vs. Dự đoán của AI (30 ngày qua)</h2>
              </div>
              <button
                onClick={runModelEvaluation}
                disabled={isEvaluating}
                className="btn-secondary py-1 px-3 text-xxs flex items-center gap-1"
              >
                <RefreshCw size={10} className={isEvaluating ? "animate-spin" : ""} />
                <span>Chạy lại đánh giá</span>
              </button>
            </div>

            <div className="p-4">
              {evalMetrics && (
                <div className="mb-4 p-3 bg-indigo-glow border-indigo-glow rounded-lg flex items-center justify-between">
                  <div className="text-xs text-indigo">
                    📉 Sai số tuyệt đối trung bình (MAE) của ROAS: <strong>{evalMetrics.mae_roas}</strong>
                  </div>
                  <div className="text-xxs text-zinc-500">
                    Kích thước mẫu thử nghiệm: {evalMetrics.sample_size} ngày chiến dịch
                  </div>
                </div>
              )}

              <div className="overflow-x-auto max-h-[400px]">
                <table className="products-table">
                  <thead>
                    <tr>
                      <th>Ngày</th>
                      <th>ROAS Thực tế</th>
                      <th>ROAS AI Dự đoán</th>
                      <th>Sai số ROAS</th>
                      <th>Doanh thu Thực tế</th>
                      <th>Doanh thu AI Dự đoán</th>
                      <th>Lợi nhuận Thực tế</th>
                      <th>Lợi nhuận AI Dự đoán</th>
                    </tr>
                  </thead>
                  <tbody>
                    {isEvaluating ? (
                      <tr>
                        <td colSpan={8} className="text-center py-12 text-zinc-500 text-xs">
                          Mô hình đang chạy dự đoán lặp trên dữ liệu mẫu lịch sử...
                        </td>
                      </tr>
                    ) : evalList.length === 0 ? (
                      <tr>
                        <td colSpan={8} className="text-center py-12 text-zinc-500 text-xs">
                          Nhấn nút Chạy lại đánh giá để bắt đầu so sánh dữ liệu thực tế vs dự đoán.
                        </td>
                      </tr>
                    ) : (
                      evalList.map((row, idx) => (
                        <tr key={idx}>
                          <td className="font-mono text-xxs font-bold text-violet whitespace-nowrap">{row.date}</td>
                          <td className="font-bold text-xs">{row.actual_roas}x</td>
                          <td className="text-indigo font-bold text-xs">{row.predicted_roas}x</td>
                          <td>
                            <span className={`text-xxs font-bold px-2 py-0.5 rounded-full ${
                              row.error_pct < 5.0 ? "bg-success-glow text-success" :
                              row.error_pct < 15.0 ? "bg-warning-glow text-warning" :
                              "bg-error-glow text-error"
                            }`}>
                              ±{row.error_pct}% ({Math.abs(row.actual_roas - row.predicted_roas).toFixed(2)})
                            </span>
                          </td>
                          <td className="text-xs">{Math.round(row.actual_gmv).toLocaleString("vi-VN")}đ</td>
                          <td className="text-zinc-500 text-xs">{Math.round(row.predicted_gmv).toLocaleString("vi-VN")}đ</td>
                          <td className="text-xs">{Math.round(row.actual_profit).toLocaleString("vi-VN")}đ</td>
                          <td className="text-zinc-500 text-xs">{Math.round(row.predicted_profit).toLocaleString("vi-VN")}đ</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ----------------- SUB-TAB 3: PREDICTIONS & RECOMMENDATIONS ----------------- */}
      {activeSubTab === "prediction" && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Simulation Inputs */}
          <div className="section-card input-panel-card h-fit">
            <div className="panel-header">
              <Sparkles size={18} className="header-icon text-warning" />
              <h2>Thiết lập phễu & Mục tiêu dự đoán</h2>
            </div>
            <div className="p-4 flex flex-col gap-4">
              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-1">
                  <label className="text-xs font-semibold">CTR muốn giả định (%)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={currCtr}
                    onChange={(e) => setCurrCtr(Number(e.target.value))}
                    className="form-input text-xs"
                  />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-xs font-semibold">CVR muốn giả định (%)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={currCvr}
                    onChange={(e) => setCurrCvr(Number(e.target.value))}
                    className="form-input text-xs"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-1">
                  <label className="text-xs font-bold text-violet">Chi phí CPA giả định (đ)</label>
                  <input
                    type="number"
                    value={currCpa}
                    onChange={(e) => setCurrCpa(Number(e.target.value))}
                    className="form-input text-xs border-violet-glow"
                  />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-xs font-semibold">Tỷ lệ hoàn trả (%)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={currRefund}
                    onChange={(e) => setCurrRefund(Number(e.target.value))}
                    className="form-input text-xs"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 border-t pt-3">
                <div className="flex flex-col gap-1">
                  <label className="text-xs font-semibold text-amber">Mục tiêu ROAS tối thiểu</label>
                  <input
                    type="number"
                    step="0.1"
                    value={targetRoas}
                    onChange={(e) => setTargetRoas(Number(e.target.value))}
                    className="form-input text-xs border-warning-glow bg-warning-glow text-amber font-bold"
                  />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-xs font-semibold text-amber">Lợi nhuận mục tiêu (đ)</label>
                  <input
                    type="number"
                    value={targetProfit}
                    onChange={(e) => setTargetProfit(Number(e.target.value))}
                    className="form-input text-xs border-warning-glow bg-warning-glow text-amber font-bold"
                  />
                </div>
              </div>

              <button
                onClick={handleGetRecommendations}
                disabled={isAnalyzing || isTraining}
                className="btn-primary py-2 px-4 flex items-center justify-center gap-2 mt-2 w-full text-sm font-bold bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600"
              >
                {isAnalyzing ? (
                  <>
                    <RefreshCw size={16} className="animate-spin" />
                    <span>Đang tính toán tối ưu...</span>
                  </>
                ) : (
                  <>
                    <Activity size={16} />
                    <span>Phân Tích & Gợi Ý ROAS Hợp Lý</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Predictor & Optimization Output Results */}
          <div className="flex flex-col gap-6">
            {optimizedResults ? (
              <div className="section-card input-panel-card border-success-highlight">
                <div className="panel-header">
                  <CheckCircle2 size={20} className="header-icon text-success" />
                  <h2>Khuyến nghị tối ưu thầu từ AI</h2>
                </div>

                <div className="p-4">
                  <div className="stats-grid-light mb-6">
                    <div className="stats-card-light">
                      <span className="label">ROAS Phù Hợp gợi ý</span>
                      <span className="val text-success">{optimizedResults.optimized_predictions.roas}x</span>
                    </div>
                    <div className="stats-card-light">
                      <span className="label">Lợi nhuận ước tính</span>
                      <span className="val text-violet">
                        {Math.round(optimizedResults.optimized_predictions.profit).toLocaleString("vi-VN")}đ
                      </span>
                    </div>
                    <div className="stats-card-light">
                      <span className="label">Độ tin cậy dự báo</span>
                      <span className="val text-amber">{optimizedResults.optimized_predictions.confidence}%</span>
                    </div>
                  </div>

                  <h3 className="text-xs font-bold mb-3 flex items-center gap-1.5 border-b pb-2 text-violet">
                    <TrendingUp size={14} className="text-violet" />
                    <span>Hành động cần làm để tối ưu phễu Ads:</span>
                  </h3>

                  <div className="recommendations-wrapper">
                    {recommendations.map((rec) => (
                      <div 
                        key={rec.priority}
                        className="recommendation-card"
                      >
                        <div className="recommendation-badge-priority">
                          {rec.priority}
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center justify-between flex-wrap gap-2 mb-1">
                            <span className="text-xs font-bold">{rec.action}</span>
                            <div className="flex items-center gap-2">
                              <span className="text-[10px] bg-success-glow text-success px-2 py-0.5 rounded-full font-bold">
                                Lợi nhuận: {rec.expected_profit}
                              </span>
                              <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${
                                rec.difficulty === "Low" ? "bg-success-glow text-success" :
                                rec.difficulty === "Medium" ? "bg-warning-glow text-warning" :
                                "bg-error-glow text-error"
                              }`}>
                                Độ khó: {rec.difficulty}
                              </span>
                            </div>
                          </div>
                          <p className="text-xxs text-zinc-500 leading-relaxed">{rec.reason}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="section-card input-panel-card p-8 text-center text-zinc-500 text-xs flex flex-col items-center justify-center gap-2">
                <Sparkles size={24} className="text-zinc-600 animate-pulse" />
                <span>Hãy thiết lập mục tiêu ở bên trái và bấm Phân Tích để AI tính toán thầu tối ưu.</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {showEditModal && editingRecord && (
        <div className="modal-backdrop">
          <div className="modal-container max-w-lg">
            <div className="modal-header">
              <h3>Sửa chỉ số Chiến dịch</h3>
              <button 
                onClick={() => setShowEditModal(false)}
                className="text-zinc-500 hover:text-zinc-300 font-bold"
              >
                ✕
              </button>
            </div>
            <form onSubmit={handleUpdateRecordSubmit} className="modal-form">
              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-1">
                  <label className="text-xs font-semibold text-zinc-400 font-bold">ID sản phẩm chạy ADS</label>
                  <input
                    type="text"
                    value={editProductId}
                    onChange={(e) => setEditProductId(e.target.value)}
                    className="form-input text-xs"
                    required
                  />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-xs font-semibold text-zinc-400 font-bold">Ngày chạy (YYYY-MM-DD)</label>
                  <input
                    type="text"
                    value={editDate}
                    onChange={(e) => setEditDate(e.target.value)}
                    className="form-input text-xs"
                    required
                  />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-xs font-semibold text-zinc-400 font-bold">Tỉ lệ CTR (%)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={editCtr}
                    onChange={(e) => setEditCtr(Number(e.target.value))}
                    className="form-input text-xs"
                    required
                  />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-xs font-semibold text-zinc-400 font-bold">Tỉ lệ CVR (%)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={editCvr}
                    onChange={(e) => setEditCvr(Number(e.target.value))}
                    className="form-input text-xs"
                    required
                  />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-xs font-semibold text-zinc-400 font-bold">Giá thầu CPC (đ)</label>
                  <input
                    type="number"
                    value={editCpc}
                    onChange={(e) => setEditCpc(Number(e.target.value))}
                    className="form-input text-xs"
                    required
                  />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-xs font-semibold text-zinc-400 font-bold">Giá mỗi Action CPA (đ)</label>
                  <input
                    type="number"
                    value={editCpa}
                    onChange={(e) => setEditCpa(Number(e.target.value))}
                    className="form-input text-xs"
                    required
                  />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-xs font-semibold text-zinc-400 font-bold">ROAS Thực tế</label>
                  <input
                    type="number"
                    step="0.01"
                    value={editRoas}
                    onChange={(e) => setEditRoas(Number(e.target.value))}
                    className="form-input text-xs"
                    required
                  />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-xs font-semibold text-zinc-400 font-bold">Tỉ lệ hoàn hàng (%)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={editRefund}
                    onChange={(e) => setEditRefund(Number(e.target.value))}
                    className="form-input text-xs"
                    required
                  />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-xs font-semibold text-zinc-400 font-bold">Doanh thu GMV (đ)</label>
                  <input
                    type="number"
                    value={editGmv}
                    onChange={(e) => setEditGmv(Number(e.target.value))}
                    className="form-input text-xs"
                    required
                  />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-xs font-semibold text-zinc-400 font-bold">Lợi nhuận ước tính (đ)</label>
                  <input
                    type="number"
                    value={editProfit}
                    onChange={(e) => setEditProfit(Number(e.target.value))}
                    className="form-input text-xs"
                    required
                  />
                </div>
              </div>
              <div className="modal-footer mt-4">
                <button 
                  type="button" 
                  onClick={() => setShowEditModal(false)}
                  className="btn-secondary text-xs px-4 py-2 border border-zinc-800 hover:bg-zinc-800"
                >
                  Hủy
                </button>
                <button 
                  type="submit" 
                  className="btn-primary text-xs px-4 py-2 bg-gradient-to-r from-violet-600 to-indigo-600 font-bold"
                >
                  Lưu thay đổi
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
