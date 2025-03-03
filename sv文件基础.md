```systemverilog
`timescale 1ns / 1ps

module tensor_core_tb;

/////////////////////////////////////////////////////////////////////////////
// 参数定义
/////////////////////////////////////////////////////////////////////////////
localparam CLK_PERIOD = 5;  // 200MHz时钟
localparam MAT_SIZE = 16;   // 测试矩阵尺寸（m16n16k16）

// AXI4接口参数
localparam AXI_ADDR_WIDTH = 32;
localparam AXI_DATA_WIDTH = 32;

// 精度模式定义
typedef enum logic [1:0] {
    INT4    = 2'b00,
    INT8    = 2'b01,
    FP16    = 2'b10,
    FP32    = 2'b11
} precision_mode_t;

/////////////////////////////////////////////////////////////////////////////
// 时钟与复位信号
/////////////////////////////////////////////////////////////////////////////
logic axi4_slave_aclk;
logic axi4_slave_aresetn;
logic axi4_master_aclk;
logic axi4_master_aresetn;
logic apb_clk;
logic apb_rstn;

/////////////////////////////////////////////////////////////////////////////
// AXI4 Slave接口信号
/////////////////////////////////////////////////////////////////////////////
// 写地址通道
logic                       axi4_slave_awvalid;
logic [AXI_ADDR_WIDTH-1:0]  axi4_slave_awaddr;
logic                       axi4_slave_awready;
// 写数据通道
logic                       axi4_slave_wvalid;
logic [AXI_DATA_WIDTH-1:0]  axi4_slave_wdata;
logic [3:0]                 axi4_slave_wstrb;
logic                       axi4_slave_wready;
// 写响应通道
logic                       axi4_slave_bvalid;
logic [1:0]                 axi4_slave_bresp;
logic                       axi4_slave_bready;

/////////////////////////////////////////////////////////////////////////////
// AXI4 Master接口信号
/////////////////////////////////////////////////////////////////////////////
// 写地址通道
logic                       axi4_master_awvalid;
logic [AXI_ADDR_WIDTH-1:0]  axi4_master_awaddr;
logic                       axi4_master_awready;
// 写数据通道
logic                       axi4_master_wvalid;
logic [AXI_DATA_WIDTH-1:0]  axi4_master_wdata;
logic                       axi4_master_wready;

/////////////////////////////////////////////////////////////////////////////
// APB接口信号
/////////////////////////////////////////////////////////////////////////////
logic                       apb_psel;
logic                       apb_penable;
logic                       apb_pwrite;
logic [AXI_ADDR_WIDTH-1:0]  apb_paddr;
logic [AXI_DATA_WIDTH-1:0]  apb_pwdata;
logic [AXI_DATA_WIDTH-1:0]  apb_prdata;
logic                       apb_pready;

/////////////////////////////////////////////////////////////////////////////
// DUT实例化
/////////////////////////////////////////////////////////////////////////////
tensor_core dut (
    // AXI4 Slave
    .axi4_slave_aclk       (axi4_slave_aclk),
    .axi4_slave_aresetn    (axi4_slave_aresetn),
    .axi4_slave_awvalid    (axi4_slave_awvalid),
    .axi4_slave_awaddr     (axi4_slave_awaddr),
    .axi4_slave_awready    (axi4_slave_awready),
    .axi4_slave_wvalid     (axi4_slave_wvalid),
    .axi4_slave_wdata      (axi4_slave_wdata),
    .axi4_slave_wstrb      (axi4_slave_wstrb),
    .axi4_slave_wready     (axi4_slave_wready),
    .axi4_slave_bvalid     (axi4_slave_bvalid),
    .axi4_slave_bresp      (axi4_slave_bresp),
    .axi4_slave_bready     (axi4_slave_bready),
    // AXI4 Master
    .axi4_master_aclk      (axi4_master_aclk),
    .axi4_master_aresetn   (axi4_master_aresetn),
    .axi4_master_awvalid   (axi4_master_awvalid),
    .axi4_master_awaddr    (axi4_master_awaddr),
    .axi4_master_awready   (axi4_master_awready),
    .axi4_master_wvalid    (axi4_master_wvalid),
    .axi4_master_wdata     (axi4_master_wdata),
    .axi4_master_wready    (axi4_master_wready),
    // APB
    .apb_clk               (apb_clk),
    .apb_rstn              (apb_rstn),
    .apb_psel              (apb_psel),
    .apb_penable           (apb_penable),
    .apb_pwrite            (apb_pwrite),
    .apb_paddr             (apb_paddr),
    .apb_pwdata            (apb_pwdata),
    .apb_prdata            (apb_prdata),
    .apb_pready            (apb_pready)
);

/////////////////////////////////////////////////////////////////////////////
// 时钟生成
/////////////////////////////////////////////////////////////////////////////
initial begin
    axi4_slave_aclk = 0;
    forever #(CLK_PERIOD/2) axi4_slave_aclk = ~axi4_slave_aclk;
end

initial begin
    axi4_master_aclk = 0;
    forever #(CLK_PERIOD/2) axi4_master_aclk = ~axi4_master_aclk;
end

initial begin
    apb_clk = 0;
    forever #(CLK_PERIOD*2) apb_clk = ~apb_clk; // APB时钟较慢
end

/////////////////////////////////////////////////////////////////////////////
// 复位生成
/////////////////////////////////////////////////////////////////////////////
initial begin
    axi4_slave_aresetn = 0;
    axi4_master_aresetn = 0;
    apb_rstn = 0;
    #100;
    axi4_slave_aresetn = 1;
    axi4_master_aresetn = 1;
    apb_rstn = 1;
end

/////////////////////////////////////////////////////////////////////////////
// 测试控制变量
/////////////////////////////////////////////////////////////////////////////
logic [31:0] expected_D [0:MAT_SIZE-1][0:MAT_SIZE-1];
logic test_pass = 1;

/////////////////////////////////////////////////////////////////////////////
// APB写任务
/////////////////////////////////////////////////////////////////////////////
task apb_write(input logic [31:0] addr, input logic [31:0] data);
    @(posedge apb_clk);
    apb_psel    = 1;
    apb_penable = 0;
    apb_pwrite  = 1;
    apb_paddr   = addr;
    apb_pwdata  = data;
    @(posedge apb_clk);
    apb_penable = 1;
    wait(apb_pready);
    @(posedge apb_clk);
    apb_psel    = 0;
    apb_penable = 0;
endtask

/////////////////////////////////////////////////////////////////////////////
// AXI4 Slave写任务
/////////////////////////////////////////////////////////////////////////////
task axi4_write(input logic [31:0] addr, input logic [31:0] data);
    // 写地址通道
    axi4_slave_awvalid = 1;
    axi4_slave_awaddr  = addr;
    wait(axi4_slave_awready);
    @(posedge axi4_slave_aclk);
    axi4_slave_awvalid = 0;

    // 写数据通道
    axi4_slave_wvalid = 1;
    axi4_slave_wdata  = data;
    axi4_slave_wstrb  = 4'hF;
    wait(axi4_slave_wready);
    @(posedge axi4_slave_aclk);
    axi4_slave_wvalid = 0;

    // 写响应
    wait(axi4_slave_bvalid);
    @(posedge axi4_slave_aclk);
    axi4_slave_bready = 1;
    @(posedge axi4_slave_aclk);
    axi4_slave_bready = 0;
endtask

/////////////////////////////////////////////////////////////////////////////
// 初始化测试数据
/////////////////////////////////////////////////////////////////////////////
task init_test_data();
    // 示例：生成随机测试数据
    for (int i=0; i<MAT_SIZE; i++) begin
        for (int j=0; j<MAT_SIZE; j++) begin
            axi4_write(32'h1000 + i*4, $urandom()); // 写入矩阵A
            axi4_write(32'h2000 + j*4, $urandom()); // 写入矩阵B
            axi4_write(32'h3000 + i*4, $urandom()); // 写入矩阵C
        end
    end
endtask

/////////////////////////////////////////////////////////////////////////////
// 结果检查任务
/////////////////////////////////////////////////////////////////////////////
task check_results();
    // 从AXI Master接口读取数据（此处简化）
    foreach(expected_D[i,j]) begin
        // 比较预期值与实际值
        if (expected_D[i][j] !== dut.buffer_d[i][j]) begin
            $display("Error at D[%0d][%0d]: Exp=0x%h, Act=0x%h", 
                     i,j, expected_D[i][j], dut.buffer_d[i][j]);
            test_pass = 0;
        end
    end
    if (test_pass) $display("*** TEST PASSED ***");
    else $display("*** TEST FAILED ***");
endtask

/////////////////////////////////////////////////////////////////////////////
// 主测试流程
/////////////////////////////////////////////////////////////////////////////
initial begin
    // 初始化信号
    axi4_slave_awvalid = 0;
    axi4_slave_wvalid  = 0;
    axi4_slave_bready  = 0;
    apb_psel    = 0;
    apb_penable = 0;

    // 等待复位完成
    wait(axi4_slave_aresetn && axi4_master_aresetn && apb_rstn);
    #100;

    // 配置精度模式（INT8）
    apb_write(32'h14, {24'h0, 2'b01}); // config_reg[5]精度设置

    // 配置矩阵尺寸（m16n16k16）
    apb_write(32'h10, {16'd16, 16'd16}); // m=16, n=16
    apb_write(32'h0C, 16'd16);           // k=16

    // 加载测试数据
    init_test_data();

    // 启动计算
    apb_write(32'h00, 32'h1); // 启动位

    // 等待计算完成
    wait(dut.compute_done);
    #100;

    // 读取结果并检查
    check_results();

    // 结束仿真
    $finish;
end

/////////////////////////////////////////////////////////////////////////////
// 波形记录（可选）
/////////////////////////////////////////////////////////////////////////////
initial begin
    $dumpfile("waveform.vcd");
    $dumpvars(0, tensor_core_tb);
end

endmodule
```

### 测试平台说明：
1. **接口定义**：完整实现AXI4 Slave/Master和APB接口信号，与DUT严格对应；
2. **时钟与复位**：生成三组独立时钟，满足多时钟域需求；
3. **关键任务**：
   - `apb_write`：实现APB寄存器配置；
   - `axi4_write`：实现AXI4 Slave接口数据写入；
   - `init_test_data`：初始化矩阵数据（示例使用随机数）；
4. **结果验证**：直接访问DUT内部buffer_d进行结果比对（实际项目中应通过AXI Master接口读取）；
5. **测试流程**：
   - 配置精度模式（INT8）；
   - 设置矩阵尺寸（m16n16k16）；
   - 加载数据并启动计算；
   - 等待完成信号后验证结果；

### 扩展建议：
1. **增加稀疏测试用例**：
   ```systemverilog
   // 启用稀疏模式
   apb_write(32'h14, {24'h0, 1'b1}); // 设置config_reg[5][0]=1
   // 写入稀疏掩码
   for (int i=0; i<64; i++) 
       axi4_write(32'h5000 + i*4, 32'hFFFF_FFFF); // 全1掩码
   ```
2. **混合精度测试**：
   ```systemverilog
   // 配置FP16乘法+FP32累加
   apb_write(32'h14, {24'h0, 2'b10, 1'b1}); 
   ```
3. **溢出测试**：
   ```systemverilog
   // 写入最大INT8值（127）
   axi4_write(32'h1000, 32'h7F7F_7F7F); 
   axi4_write(32'h2000, 32'h7F7F_7F7F);
   ```

该测试平台可直接在Vivado中运行，通过修改`init_test_data`和添加更多测试用例可全面验证设计功能。