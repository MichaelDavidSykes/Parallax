import { AfterViewInit, Component, ElementRef, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { ColorType, IChartApi, ISeriesApi, UTCTimestamp, createChart } from 'lightweight-charts';

import { Trading212Summary, Trading212Trade, TradingChart } from '../models/api.models';
import { ParallaxApiService } from '../services/parallax-api.service';

@Component({
  selector: 'app-trading',
  templateUrl: './trading.component.html',
  styleUrls: ['./trading.component.scss']
})
export class TradingComponent implements OnInit, AfterViewInit, OnDestroy {
  @ViewChild('chartHost') chartHost?: ElementRef<HTMLDivElement>;

  public loading = false;
  public placingOrder = false;
  public error = '';
  public orderStatus = '';
  public summary: Trading212Summary | null = null;
  public chartData: TradingChart | null = null;
  public tickers: string[] = [];
  public selectedTicker = '';
  public timeframe = '1M';
  public chartMode: 'candles' | 'line' = 'candles';
  public readonly timeframes = ['1D', '1W', '1M', '3M', '1Y', 'ALL'];
  public order = {
    ticker: '',
    side: 'BUY',
    quantity: 1,
    extended_hours: false
  };

  private chart?: IChartApi;
  private candleSeries?: ISeriesApi<'Candlestick'>;
  private lineSeries?: ISeriesApi<'Line'>;
  private resizeObserver?: ResizeObserver;

  constructor(private api: ParallaxApiService) {}

  ngOnInit(): void {
    this.loadSummary();
  }

  ngAfterViewInit(): void {
    this.initChart();
  }

  ngOnDestroy(): void {
    this.resizeObserver?.disconnect();
    this.chart?.remove();
  }

  public loadSummary(): void {
    this.loading = true;
    this.error = '';
    this.api.trading212Summary().subscribe({
      next: summary => {
        this.summary = summary;
        this.tickers = this.uniqueTickers(summary);
        if (!this.selectedTicker && this.tickers.length) {
          this.selectedTicker = this.tickers[0];
        }
        this.order.ticker = this.selectedTicker;
        this.loading = false;
        this.loadChart();
      },
      error: err => {
        this.error = err?.error?.detail || err?.message || 'Trading 212 is not reachable.';
        this.loading = false;
      }
    });
  }

  public loadChart(): void {
    this.loading = true;
    this.error = '';
    this.api.tradingChart(this.selectedTicker, this.timeframe).subscribe({
      next: chartData => {
        this.chartData = chartData;
        this.order.ticker = chartData.ticker || this.selectedTicker || this.order.ticker;
        this.selectedTicker = chartData.ticker || this.selectedTicker;
        this.loading = false;
        this.renderChart();
      },
      error: err => {
        this.error = err?.error?.detail || err?.message || 'Chart data is not reachable.';
        this.loading = false;
      }
    });
  }

  public setTimeframe(timeframe: string): void {
    this.timeframe = timeframe;
    this.loadChart();
  }

  public setChartMode(mode: 'candles' | 'line'): void {
    this.chartMode = mode;
    this.renderChart();
  }

  public onTickerChange(ticker: string): void {
    this.selectedTicker = ticker;
    this.order.ticker = ticker;
    this.loadChart();
  }

  public placeOrder(): void {
    this.placingOrder = true;
    this.error = '';
    this.orderStatus = '';
    this.api.placeMarketOrder(this.order).subscribe({
      next: () => {
        this.orderStatus = 'Order sent';
        this.placingOrder = false;
        this.loadSummary();
      },
      error: err => {
        this.error = err?.error?.detail || err?.message || 'Order was not placed.';
        this.placingOrder = false;
      }
    });
  }

  public get trades(): Trading212Trade[] {
    return this.chartData?.trades || [];
  }

  public get currencySymbol(): string {
    const currency = this.summary?.currency || 'USD';
    return currency === 'GBP' ? '£' : currency === 'EUR' ? '€' : '$';
  }

  private initChart(): void {
    const host = this.chartHost?.nativeElement;
    if (!host || this.chart) {
      return;
    }
    this.chart = createChart(host, {
      width: host.clientWidth,
      height: host.clientHeight,
      layout: {
        background: { type: ColorType.Solid, color: '#050505' },
        textColor: '#b7b7b7'
      },
      grid: {
        vertLines: { color: 'rgba(255,255,255,0.05)' },
        horzLines: { color: 'rgba(255,255,255,0.05)' }
      },
      rightPriceScale: {
        borderColor: 'rgba(255,255,255,0.12)'
      },
      timeScale: {
        borderColor: 'rgba(255,255,255,0.12)',
        timeVisible: true
      },
      crosshair: {
        mode: 1
      }
    });
    this.candleSeries = this.chart.addCandlestickSeries({
      upColor: '#d196e6',
      borderUpColor: '#d196e6',
      wickUpColor: '#d196e6',
      downColor: '#b96470',
      borderDownColor: '#b96470',
      wickDownColor: '#b96470'
    });
    this.lineSeries = this.chart.addLineSeries({
      color: '#d196e6',
      lineWidth: 2
    });
    this.resizeObserver = new ResizeObserver(entries => {
      const size = entries[0]?.contentRect;
      if (size) {
        this.chart?.applyOptions({ width: size.width, height: size.height });
      }
    });
    this.resizeObserver.observe(host);
    this.renderChart();
  }

  private renderChart(): void {
    if (!this.chart || !this.candleSeries || !this.lineSeries || !this.chartData) {
      return;
    }
    const candles = this.chartData.candles.map(item => ({
      time: item.time as UTCTimestamp,
      open: item.open,
      high: item.high,
      low: item.low,
      close: item.close
    }));
    const line = this.chartData.line.map(item => ({
      time: item.time as UTCTimestamp,
      value: item.value
    }));
    this.candleSeries.setData(candles);
    this.lineSeries.setData(line);
    this.candleSeries.applyOptions({ visible: this.chartMode === 'candles' });
    this.lineSeries.applyOptions({ visible: this.chartMode === 'line' });
    this.candleSeries.setMarkers(this.tradeMarkers());
    if (candles.length || line.length) {
      this.chart.timeScale().fitContent();
    }
  }

  private tradeMarkers() {
    return this.trades
      .map(trade => {
        const time = this.toTimestamp(trade.executed_at);
        if (!time) {
          return null;
        }
        return {
          time: time as UTCTimestamp,
          position: trade.side === 'SELL' ? 'aboveBar' : 'belowBar',
          color: trade.side === 'SELL' ? '#b96470' : '#d196e6',
          shape: trade.side === 'SELL' ? 'arrowDown' : 'arrowUp',
          text: `${trade.side} ${trade.quantity}`
        };
      })
      .filter(Boolean) as any;
  }

  private toTimestamp(value: string): number | null {
    const date = new Date(value);
    const timestamp = Math.floor(date.getTime() / 1000);
    return Number.isFinite(timestamp) ? timestamp : null;
  }

  private uniqueTickers(summary: Trading212Summary): string[] {
    const values = [
      ...summary.positions.map(position => position.symbol),
      ...summary.trades.map(trade => trade.symbol)
    ].filter(Boolean);
    return Array.from(new Set(values));
  }
}
