import React, { useState, useRef } from "react";
import { TrendingUp, Award, BarChart3, Activity } from "lucide-react";

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

interface DashboardChartsProps {
  dataset: DatasetRecord[];
}

export const DashboardCharts: React.FC<DashboardChartsProps> = ({ dataset }) => {
  // Sort dataset chronologically
  const sortedData = [...dataset].sort(
    (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()
  );

  if (dataset.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-12 bg-white border border-slate-200 rounded-2xl text-slate-400">
        <BarChart3 size={48} className="text-slate-300 mb-3" />
        <p className="text-sm font-semibold">Chưa có dữ liệu để hiển thị biểu đồ</p>
        <p className="text-xs text-slate-400 mt-1">Vui lòng nhập chỉ số chiến dịch trong tab Bảng dữ liệu</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6 w-full">
      {/* Grid containing TimeTrend and CTR/CVR trends */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Chart 1: GMV & Profit Trend */}
        <div className="input-panel-card" style={{ padding: "1.5rem" }}>
          <div className="panel-header justify-between">
            <div className="flex items-center gap-2">
              <TrendingUp size={18} className="header-icon text-indigo" />
              <h2 className="text-sm font-bold text-slate-800">Xu hướng GMV & Lợi nhuận Ròng</h2>
            </div>
            <div className="flex items-center gap-3 text-xxs font-semibold">
              <div className="flex items-center gap-1">
                <span className="w-2.5 h-2.5 rounded-full bg-blue-500 inline-block"></span>
                <span className="text-slate-500">GMV</span>
              </div>
              <div className="flex items-center gap-1">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block"></span>
                <span className="text-slate-500">Lợi nhuận</span>
              </div>
            </div>
          </div>
          <div className="relative mt-2" style={{ height: "260px" }}>
            <TimeTrendChart data={sortedData} />
          </div>
        </div>

        {/* Chart 2: CTR & CVR Trend */}
        <div className="input-panel-card" style={{ padding: "1.5rem" }}>
          <div className="panel-header justify-between">
            <div className="flex items-center gap-2">
              <Activity size={18} className="header-icon text-violet" />
              <h2 className="text-sm font-bold text-slate-800">Tỉ lệ CTR % & CVR % theo Ngày</h2>
            </div>
            <div className="flex items-center gap-3 text-xxs font-semibold">
              <div className="flex items-center gap-1">
                <span className="w-2.5 h-2.5 rounded-full bg-sky-500 inline-block"></span>
                <span className="text-slate-500">CTR %</span>
              </div>
              <div className="flex items-center gap-1">
                <span className="w-2.5 h-2.5 rounded-full bg-purple-500 inline-block"></span>
                <span className="text-slate-500">CVR %</span>
              </div>
            </div>
          </div>
          <div className="relative mt-2" style={{ height: "260px" }}>
            <ConversionChart data={sortedData} />
          </div>
        </div>
      </div>

      {/* Chart 3: Product Profit Contribution */}
      <div className="input-panel-card" style={{ padding: "1.5rem" }}>
        <div className="panel-header justify-between">
          <div className="flex items-center gap-2">
            <Award size={18} className="header-icon text-amber" />
            <h2 className="text-sm font-bold text-slate-800">Đóng góp Lợi nhuận ròng của các Sản phẩm (Top 5)</h2>
          </div>
        </div>
        <div className="mt-2">
          <ProductBarChart data={sortedData} />
        </div>
      </div>
    </div>
  );
};

// ==========================================
// 1. TimeTrendChart (GMV & Profit) Component
// ==========================================
const TimeTrendChart: React.FC<{ data: DatasetRecord[] }> = ({ data }) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });

  const width = 500;
  const height = 240;
  const paddingLeft = 55;
  const paddingRight = 15;
  const paddingTop = 15;
  const paddingBottom = 30;

  const chartWidth = width - paddingLeft - paddingRight;
  const chartHeight = height - paddingTop - paddingBottom;

  // Find Min & Max
  const maxGMV = Math.max(...data.map((d) => d.gmv), 1000000);
  const maxProfit = Math.max(...data.map((d) => d.profit), 0);
  const minProfit = Math.min(...data.map((d) => d.profit), 0);
  
  const yMax = Math.max(maxGMV, maxProfit) * 1.15;
  const yMin = minProfit < 0 ? minProfit * 1.2 : 0;
  const yRange = yMax - yMin;

  // Coordinate converters
  const getX = (index: number) => {
    if (data.length <= 1) return paddingLeft + chartWidth / 2;
    return paddingLeft + (index / (data.length - 1)) * chartWidth;
  };

  const getY = (val: number) => {
    const ratio = (val - yMin) / yRange;
    return height - paddingBottom - ratio * chartHeight;
  };

  // Helper for nice date format
  const formatDate = (dateStr: string) => {
    try {
      const d = new Date(dateStr);
      return `${d.getDate()}/${d.getMonth() + 1}`;
    } catch {
      return dateStr;
    }
  };

  // Generate SVG paths
  let gmvAreaPath = "";
  let gmvLinePath = "";
  let profitLinePath = "";

  if (data.length > 0) {
    // GMV Line and Area
    const pointsGMV = data.map((d, i) => `${getX(i)},${getY(d.gmv)}`);
    gmvLinePath = `M ${pointsGMV.join(" L ")}`;
    gmvAreaPath = `${gmvLinePath} L ${getX(data.length - 1)},${getY(yMin)} L ${getX(0)},${getY(yMin)} Z`;

    // Profit Line
    const pointsProfit = data.map((d, i) => `${getX(i)},${getY(d.profit)}`);
    profitLinePath = `M ${pointsProfit.join(" L ")}`;
  }

  // Handle Hover Interaction
  const handleMouseMove = (e: React.MouseEvent<SVGSVGElement, MouseEvent>) => {
    if (!svgRef.current || data.length === 0) return;
    const rect = svgRef.current.getBoundingClientRect();
    const clientX = e.clientX - rect.left;
    const svgX = (clientX / rect.width) * width;

    // Calculate nearest data point
    const relativeX = svgX - paddingLeft;
    const index = Math.round((relativeX / chartWidth) * (data.length - 1));
    const clampedIndex = Math.max(0, Math.min(data.length - 1, index));

    setHoverIndex(clampedIndex);
    
    // Set Tooltip coordinates
    const tooltipX = getX(clampedIndex);
    const tooltipY = getY(Math.max(data[clampedIndex].gmv, data[clampedIndex].profit)) - 10;
    
    // Adjust tooltip position within boundary
    setTooltipPos({
      x: tooltipX > width - 150 ? tooltipX - 140 : tooltipX + 10,
      y: tooltipY < 60 ? tooltipY + 40 : tooltipY - 50,
    });
  };

  const handleMouseLeave = () => {
    setHoverIndex(null);
  };

  // Generates 4 horizontal gridlines
  const gridLines = [];
  for (let i = 0; i <= 3; i++) {
    const val = yMin + (yRange / 3) * i;
    gridLines.push({
      y: getY(val),
      label: val >= 1000000 
        ? `${(val / 1000000).toFixed(1)}M` 
        : val >= 1000 
        ? `${(val / 1000).toFixed(0)}k` 
        : val.toFixed(0),
    });
  }

  return (
    <div className="w-full h-full relative">
      <svg
        ref={svgRef}
        viewBox={`0 0 ${width} ${height}`}
        className="w-full h-full"
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        style={{ overflow: "visible" }}
      >
        <defs>
          {/* GMV Gradient */}
          <linearGradient id="gmvGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.25" />
            <stop offset="100%" stopColor="#3b82f6" stopOpacity="0.0" />
          </linearGradient>
          {/* Profit glow filter */}
          <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>

        {/* Gridlines */}
        {gridLines.map((line, idx) => (
          <g key={idx}>
            <line
              x1={paddingLeft}
              y1={line.y}
              x2={width - paddingRight}
              y2={line.y}
              stroke="#e2e8f0"
              strokeDasharray="4,4"
              strokeWidth="0.8"
            />
            <text
              x={paddingLeft - 8}
              y={line.y + 3}
              textAnchor="end"
              fill="#94a3b8"
              fontSize="8"
              fontWeight="bold"
            >
              {line.label}
            </text>
          </g>
        ))}

        {/* X Axis Line */}
        <line
          x1={paddingLeft}
          y1={getY(0)}
          x2={width - paddingRight}
          y2={getY(0)}
          stroke="#cbd5e1"
          strokeWidth="1"
        />

        {/* GMV Area & Line */}
        {gmvAreaPath && (
          <path d={gmvAreaPath} fill="url(#gmvGrad)" />
        )}
        {gmvLinePath && (
          <path
            d={gmvLinePath}
            fill="none"
            stroke="#3b82f6"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        )}

        {/* Profit Line */}
        {profitLinePath && (
          <path
            d={profitLinePath}
            fill="none"
            stroke="#10b981"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        )}

        {/* X Axis Labels */}
        {data.map((d, i) => {
          // Show label if it's start, end, or middle data to avoid clutter
          const showLabel = 
            data.length < 8 || 
            i === 0 || 
            i === data.length - 1 || 
            (data.length >= 8 && i % Math.floor(data.length / 4) === 0);
          
          if (!showLabel) return null;

          return (
            <text
              key={i}
              x={getX(i)}
              y={height - 12}
              textAnchor="middle"
              fill="#94a3b8"
              fontSize="8"
              fontWeight="600"
            >
              {formatDate(d.date)}
            </text>
          );
        })}

        {/* Interactive hover line & marker */}
        {hoverIndex !== null && (
          <g>
            <line
              x1={getX(hoverIndex)}
              y1={paddingTop}
              x2={getX(hoverIndex)}
              y2={height - paddingBottom}
              stroke="#6366f1"
              strokeWidth="1"
              strokeDasharray="2,2"
            />
            {/* GMV point marker */}
            <circle
              cx={getX(hoverIndex)}
              cy={getY(data[hoverIndex].gmv)}
              r="4.5"
              fill="#ffffff"
              stroke="#3b82f6"
              strokeWidth="2.5"
            />
            {/* Profit point marker */}
            <circle
              cx={getX(hoverIndex)}
              cy={getY(data[hoverIndex].profit)}
              r="4.5"
              fill="#ffffff"
              stroke="#10b981"
              strokeWidth="2.5"
            />
          </g>
        )}
      </svg>

      {/* Floating Tooltip Box */}
      {hoverIndex !== null && (
        <div
          className="absolute z-10 p-3 bg-slate-900/95 text-white border border-slate-800 rounded-xl shadow-xl flex flex-col gap-1 text-[10px] pointer-events-none transition-all duration-75"
          style={{
            left: `${(tooltipPos.x / width) * 100}%`,
            top: `${(tooltipPos.y / height) * 100}%`,
            width: "140px",
            backdropFilter: "blur(4px)",
          }}
        >
          <span className="font-bold text-slate-400 border-b border-slate-800 pb-1 mb-1 font-mono">
            Ngày {data[hoverIndex].date}
          </span>
          <div className="flex justify-between items-center mt-0.5">
            <span className="text-slate-400 font-medium">GMV:</span>
            <span className="font-bold text-sky-400">
              {Math.round(data[hoverIndex].gmv).toLocaleString("vi-VN")}đ
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-slate-400 font-medium">Lợi Nhuận:</span>
            <span className="font-bold text-emerald-400">
              {Math.round(data[hoverIndex].profit).toLocaleString("vi-VN")}đ
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-slate-400 font-medium">ROAS:</span>
            <span className="font-bold text-amber-400">{data[hoverIndex].roas}x</span>
          </div>
        </div>
      )}
    </div>
  );
};

// ==========================================
// 2. ConversionChart (CTR & CVR) Component
// ==========================================
const ConversionChart: React.FC<{ data: DatasetRecord[] }> = ({ data }) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });

  const width = 500;
  const height = 240;
  const paddingLeft = 45;
  const paddingRight = 15;
  const paddingTop = 15;
  const paddingBottom = 30;

  const chartWidth = width - paddingLeft - paddingRight;
  const chartHeight = height - paddingTop - paddingBottom;

  // Find Max Rate (CTR/CVR are in %)
  const maxRate = Math.max(...data.map((d) => Math.max(d.ctr, d.cvr)), 1);
  const yMax = maxRate * 1.15;
  const yMin = 0;
  const yRange = yMax - yMin;

  // Coordinate converters
  const getX = (index: number) => {
    if (data.length <= 1) return paddingLeft + chartWidth / 2;
    return paddingLeft + (index / (data.length - 1)) * chartWidth;
  };

  const getY = (val: number) => {
    const ratio = (val - yMin) / yRange;
    return height - paddingBottom - ratio * chartHeight;
  };

  const formatDate = (dateStr: string) => {
    try {
      const d = new Date(dateStr);
      return `${d.getDate()}/${d.getMonth() + 1}`;
    } catch {
      return dateStr;
    }
  };

  // Generate SVG lines
  let ctrLinePath = "";
  let cvrLinePath = "";

  if (data.length > 0) {
    const pointsCTR = data.map((d, i) => `${getX(i)},${getY(d.ctr)}`);
    ctrLinePath = `M ${pointsCTR.join(" L ")}`;

    const pointsCVR = data.map((d, i) => `${getX(i)},${getY(d.cvr)}`);
    cvrLinePath = `M ${pointsCVR.join(" L ")}`;
  }

  // Handle Hover Interaction
  const handleMouseMove = (e: React.MouseEvent<SVGSVGElement, MouseEvent>) => {
    if (!svgRef.current || data.length === 0) return;
    const rect = svgRef.current.getBoundingClientRect();
    const clientX = e.clientX - rect.left;
    const svgX = (clientX / rect.width) * width;

    const relativeX = svgX - paddingLeft;
    const index = Math.round((relativeX / chartWidth) * (data.length - 1));
    const clampedIndex = Math.max(0, Math.min(data.length - 1, index));

    setHoverIndex(clampedIndex);

    const tooltipX = getX(clampedIndex);
    const tooltipY = getY(Math.max(data[clampedIndex].ctr, data[clampedIndex].cvr)) - 10;

    setTooltipPos({
      x: tooltipX > width - 140 ? tooltipX - 130 : tooltipX + 10,
      y: tooltipY < 60 ? tooltipY + 40 : tooltipY - 50,
    });
  };

  const handleMouseLeave = () => {
    setHoverIndex(null);
  };

  // Generates 4 horizontal gridlines
  const gridLines = [];
  for (let i = 0; i <= 3; i++) {
    const val = yMin + (yRange / 3) * i;
    gridLines.push({
      y: getY(val),
      label: `${val.toFixed(1)}%`,
    });
  }

  return (
    <div className="w-full h-full relative">
      <svg
        ref={svgRef}
        viewBox={`0 0 ${width} ${height}`}
        className="w-full h-full"
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        style={{ overflow: "visible" }}
      >
        {/* Gridlines */}
        {gridLines.map((line, idx) => (
          <g key={idx}>
            <line
              x1={paddingLeft}
              y1={line.y}
              x2={width - paddingRight}
              y2={line.y}
              stroke="#e2e8f0"
              strokeDasharray="4,4"
              strokeWidth="0.8"
            />
            <text
              x={paddingLeft - 8}
              y={line.y + 3}
              textAnchor="end"
              fill="#94a3b8"
              fontSize="8"
              fontWeight="bold"
            >
              {line.label}
            </text>
          </g>
        ))}

        {/* X Axis Line */}
        <line
          x1={paddingLeft}
          y1={height - paddingBottom}
          x2={width - paddingRight}
          y2={height - paddingBottom}
          stroke="#cbd5e1"
          strokeWidth="1"
        />

        {/* CTR Line */}
        {ctrLinePath && (
          <path
            d={ctrLinePath}
            fill="none"
            stroke="#0ea5e9"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        )}

        {/* CVR Line */}
        {cvrLinePath && (
          <path
            d={cvrLinePath}
            fill="none"
            stroke="#a855f7"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        )}

        {/* X Axis Labels */}
        {data.map((d, i) => {
          const showLabel = 
            data.length < 8 || 
            i === 0 || 
            i === data.length - 1 || 
            (data.length >= 8 && i % Math.floor(data.length / 4) === 0);
          
          if (!showLabel) return null;

          return (
            <text
              key={i}
              x={getX(i)}
              y={height - 12}
              textAnchor="middle"
              fill="#94a3b8"
              fontSize="8"
              fontWeight="600"
            >
              {formatDate(d.date)}
            </text>
          );
        })}

        {/* Interactive hover line & marker */}
        {hoverIndex !== null && (
          <g>
            <line
              x1={getX(hoverIndex)}
              y1={paddingTop}
              x2={getX(hoverIndex)}
              y2={height - paddingBottom}
              stroke="#6366f1"
              strokeWidth="1"
              strokeDasharray="2,2"
            />
            {/* CTR point marker */}
            <circle
              cx={getX(hoverIndex)}
              cy={getY(data[hoverIndex].ctr)}
              r="4.5"
              fill="#ffffff"
              stroke="#0ea5e9"
              strokeWidth="2.5"
            />
            {/* CVR point marker */}
            <circle
              cx={getX(hoverIndex)}
              cy={getY(data[hoverIndex].cvr)}
              r="4.5"
              fill="#ffffff"
              stroke="#a855f7"
              strokeWidth="2.5"
            />
          </g>
        )}
      </svg>

      {/* Floating Tooltip Box */}
      {hoverIndex !== null && (
        <div
          className="absolute z-10 p-3 bg-slate-900/95 text-white border border-slate-800 rounded-xl shadow-xl flex flex-col gap-1 text-[10px] pointer-events-none transition-all duration-75"
          style={{
            left: `${(tooltipPos.x / width) * 100}%`,
            top: `${(tooltipPos.y / height) * 100}%`,
            width: "120px",
            backdropFilter: "blur(4px)",
          }}
        >
          <span className="font-bold text-slate-400 border-b border-slate-800 pb-1 mb-1 font-mono">
            Ngày {data[hoverIndex].date}
          </span>
          <div className="flex justify-between items-center mt-0.5">
            <span className="text-slate-400 font-medium">CTR:</span>
            <span className="font-bold text-sky-400">{data[hoverIndex].ctr}%</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-slate-400 font-medium">CVR:</span>
            <span className="font-bold text-purple-400">{data[hoverIndex].cvr}%</span>
          </div>
        </div>
      )}
    </div>
  );
};

// ==========================================
// 3. ProductBarChart (Product Breakdown)
// ==========================================
const ProductBarChart: React.FC<{ data: DatasetRecord[] }> = ({ data }) => {
  // Aggregate Profit by product_id
  const summaryMap: { [key: string]: { profit: number; gmv: number } } = {};
  data.forEach((r) => {
    if (!summaryMap[r.product_id]) {
      summaryMap[r.product_id] = { profit: 0, gmv: 0 };
    }
    summaryMap[r.product_id].profit += r.profit;
    summaryMap[r.product_id].gmv += r.gmv;
  });

  const productsList = Object.keys(summaryMap)
    .map((pid) => ({
      product_id: pid,
      profit: summaryMap[pid].profit,
      gmv: summaryMap[pid].gmv,
    }))
    .sort((a, b) => b.profit - a.profit)
    .slice(0, 5);

  const maxProfit = Math.max(...productsList.map((p) => Math.abs(p.profit)), 1);

  if (productsList.length === 0) {
    return (
      <div className="text-center py-6 text-slate-400 text-xs">
        Không có dữ liệu sản phẩm.
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4 mt-2">
      {productsList.map((p, idx) => {
        // Calculate percentages
        const percentage = Math.max(2, (Math.abs(p.profit) / maxProfit) * 100);
        const isPositive = p.profit >= 0;

        return (
          <div key={idx} className="flex flex-col gap-1 bg-slate-50/50 hover:bg-slate-50 border border-slate-100 p-3 rounded-xl transition-all duration-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-5 h-5 rounded-full bg-slate-200 text-slate-700 font-bold flex items-center justify-center text-xs">
                  {idx + 1}
                </span>
                <span className="text-xs font-bold text-slate-700 font-mono truncate max-w-xs md:max-w-md">
                  {p.product_id}
                </span>
              </div>
              <div className="flex flex-col items-end">
                <span className={`text-xs font-bold ${isPositive ? "text-emerald-500" : "text-red-500"}`}>
                  {isPositive ? "+" : ""}
                  {Math.round(p.profit).toLocaleString("vi-VN")}đ
                </span>
                <span className="text-[9px] text-slate-400">GMV: {Math.round(p.gmv).toLocaleString("vi-VN")}đ</span>
              </div>
            </div>
            
            {/* The animated horizontal bar */}
            <div className="w-full bg-slate-100 rounded-full h-2.5 mt-1 overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-500 ${
                  isPositive 
                    ? "bg-gradient-to-r from-emerald-400 to-teal-500" 
                    : "bg-gradient-to-r from-red-400 to-orange-500"
                }`}
                style={{ width: `${percentage}%` }}
              ></div>
            </div>
          </div>
        );
      })}
    </div>
  );
};
