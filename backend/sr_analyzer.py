import pandas as pd
import numpy as np
from scipy.signal import find_peaks
from typing import List, Dict, Tuple, Optional, Any, Sequence
import warnings
warnings.filterwarnings('ignore')

class SupportResistanceAnalyzer:
    """
    Advanced Support and Resistance Analysis System
    Implements professional trading rules for identifying valid S&R levels
    """

    def __init__(self, zone_tolerance: float = 0.005, min_touches: int = 3):
        """
        Initialize the S&R Analyzer

        Args:
            zone_tolerance: Price tolerance for clustering levels (0.5% default)
            min_touches: Minimum touches required for a valid level
        """
        if zone_tolerance <= 0 or min_touches < 1:
            raise ValueError("zone_tolerance must be positive, min_touches >= 1")
        self.touch_tolerance = zone_tolerance
        self.cluster_tolerance = 0.01
        self.min_touches = min_touches

    def _validate_df(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate and clean DataFrame"""
        required_cols = ['High', 'Low', 'Close']
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            raise ValueError(f'Missing columns: {missing}')
        if len(df) < 20:
            raise ValueError('DataFrame must have at least 20 rows')
        for col in required_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').ffill()
        df = df.dropna(subset=required_cols)
        return df

    def identify_peaks_and_troughs(self, df: pd.DataFrame, distance: int = 10) -> Tuple[np.ndarray, np.ndarray]:
        """
        Identify swing highs and swing lows using peak detection

        Args:
            df: DataFrame with OHLC data
            distance: Minimum distance between peaks

        Returns:
            Tuple of (peak_indices, trough_indices)
        """
        df = self._validate_df(df)
        prices = df['Close'].to_numpy(dtype=float)

        if len(prices) < distance * 2 or len(np.unique(prices)) < 3:
            return np.array([]), np.array([])

        # Find peaks (resistance levels)
        peaks, _ = find_peaks(prices, distance=distance, height=np.nanpercentile(prices, 25))

        # Find troughs (support levels) by inverting the data
        troughs, _ = find_peaks(-prices, distance=distance, height=np.nanpercentile(-prices, 25))

        return peaks, troughs

    def detect_trend_pattern(self, df: pd.DataFrame, min_peaks: int = 4, distance: int = 10) -> Dict[str, Any]:
        """
        Detect uptrend (HH+HL), downtrend (LH+LL), or sideways using recent peaks/troughs.

        Args:
            df: DataFrame with OHLC data
            min_peaks: Minimum number of recent peaks/troughs to analyze
            distance: Peak detection distance

        Returns:
            {'trend_type': 'UPTREND'/'DOWNTREND'/'SIDEWAYS', 'highs': [prices], 'lows': [prices], 'high_slope': slope, 'low_slope': slope}
        """
        df = self._validate_df(df)
        peaks, troughs = self.identify_peaks_and_troughs(df, distance)
        
        high_series = df['Close'].iloc[peaks]\n        highs = np.asarray(high_series) if len(peaks) > 0 else np.array([])
        low_series = df['Close'].iloc[troughs]\n        lows = np.asarray(low_series) if len(troughs) > 0 else np.array([])

        highs = highs[~np.isnan(highs)] if len(highs) > 0 else np.array([])
        lows = lows[~np.isnan(lows)] if len(lows) > 0 else np.array([])

        # Get recent ones (most recent first)
        recent_highs = highs[-min_peaks:] if len(highs) >= min_peaks else highs
        recent_lows = lows[-min_peaks:] if len(lows) >= min_peaks else lows

        trend_type = 'SIDEWAYS'

        if len(recent_highs) >= 3 and len(recent_lows) >= 3:
            # Check sequential increases/decreases (majority)
            high_increasing = sum(recent_highs[i] > recent_highs[i-1] for i in range(1, len(recent_highs))) / (len(recent_highs)-1) > 0.6
            low_increasing = sum(recent_lows[i] > recent_lows[i-1] for i in range(1, len(recent_lows))) / (len(recent_lows)-1) > 0.6
            
            high_decreasing = sum(recent_highs[i] < recent_highs[i-1] for i in range(1, len(recent_highs))) / (len(recent_highs)-1) > 0.6
            low_decreasing = sum(recent_lows[i] < recent_lows[i-1] for i in range(1, len(recent_lows))) / (len(recent_lows)-1) > 0.6

            if high_increasing and low_increasing:
                trend_type = 'UPTREND'
            elif high_decreasing and low_decreasing:
                trend_type = 'DOWNTREND'

        # Slopes for debug
        def calc_slope(prices):
            prices = np.asarray(prices)
            if len(prices) < 2:
                return 0.0
            x = np.arange(len(prices))
            return np.polyfit(x, prices, 1)[0]

        return {
            'trend_type': trend_type,
            'highs': recent_highs.tolist(),
            'lows': recent_lows.tolist(),
            'high_slope': calc_slope(recent_highs),
            'low_slope': calc_slope(recent_lows)
        }

    def cluster_levels(self, levels: Sequence[float], tolerance: Optional[float] = None) -> List[Dict[str, Any]]: 
        """
        Cluster price levels that are within tolerance range
        """
        if tolerance is None:
            tolerance = self.cluster_tolerance

        if not levels:
            return []

        try:
            levels_array = np.asarray([float(x) for x in levels if not np.isnan(float(x))])
            if len(levels_array) == 0:
                return []
            levels_list = sorted(levels_array)

            clusters = []
            current_cluster = {'levels': [levels_list[0]], 'count': 1, 'avg_price': float(levels_list[0])}

            for level in levels_list[1:]:
                rel_diff = abs(level - current_cluster['avg_price']) / current_cluster['avg_price']
                if rel_diff <= tolerance:
                    current_cluster['levels'].append(level)
                    current_cluster['count'] += 1
                    current_cluster['avg_price'] = float(np.mean(current_cluster['levels']))
                else:
                    clusters.append(current_cluster)
                    current_cluster = {'levels': [level], 'count': 1, 'avg_price': float(level)}

            clusters.append(current_cluster)
            return clusters
        except Exception:
            return []

    def validate_level_with_three_touch_rule(self, df: pd.DataFrame, level: float,
                                           zone_tolerance: Optional[float] = None) -> Dict[str, Any]:
        """
        Validate a level using the Three Touch Rule with time spacing
        """
        if zone_tolerance is None:
            zone_tolerance = self.touch_tolerance

        zone_high = level * (1 + zone_tolerance)
        zone_low = level * (1 - zone_tolerance)

        # Vectorized touch detection
        high_mask = (df['High'] >= zone_low) & (df['High'] <= zone_high)
        low_mask = (df['Low'] >= zone_low) & (df['Low'] <= zone_high)
        close_mask = (df['Close'] >= zone_low) & (df['Close'] <= zone_high)
        
        touch_mask = high_mask | low_mask | close_mask
        touch_indices = np.where(touch_mask)[0].tolist()

        # Check time spacing
        time_spaced = self._check_time_spacing(touch_indices)

        return {
            'level': level,
            'touch_count': len(touch_indices),
            'touches': touch_indices,
            'time_spaced': time_spaced,
            'is_valid': len(touch_indices) >= self.min_touches and time_spaced
        }

    def _check_time_spacing(self, touches: List[int], min_spacing: int = 2) -> bool:
        """
        Check if touches are well-spaced in time
        """
        if len(touches) < 2:
            return True

        touches = [int(t) for t in touches]

        for i in range(1, len(touches)):
            if touches[i] - touches[i-1] < min_spacing:
                return False
        return True

    def validate_volume_confirmation(self, df: pd.DataFrame, level: float,
                                   lookback_period: int = 20) -> Dict[str, Any]:
        """
        Validate level with volume confirmation
        """
        if 'Volume' not in df.columns:
            return {'volume_confirmed': False, 'volume_ratio': 1.0}

        zone_tolerance = self.touch_tolerance
        zone_high = level * (1 + zone_tolerance)
        zone_low = level * (1 - zone_tolerance)

        touch_mask = ((df['High'] >= zone_low) & (df['High'] <= zone_high)) | \
                     ((df['Low'] >= zone_low) & (df['Low'] <= zone_high))
        
        touch_indices = np.where(touch_mask)[0]

        if len(touch_indices) == 0:
            return {'volume_confirmed': False, 'volume_ratio': 1.0}

        recent_volume = df['Volume'].tail(lookback_period).mean()
        if pd.isna(recent_volume) or recent_volume == 0:
            return {'volume_confirmed': False, 'volume_ratio': 1.0}

        touch_volumes = df['Volume'].iloc[touch_indices]
        max_touch_volume = touch_volumes.max()

        volume_ratio = max_touch_volume / recent_volume
        volume_confirmed = volume_ratio >= 1.2

        return {
            'volume_confirmed': volume_confirmed,
            'volume_ratio': volume_ratio,
            'max_touch_volume': float(max_touch_volume),
            'avg_volume': float(recent_volume)
        }

    def identify_round_number_levels(self, df: pd.DataFrame,
                                   round_numbers: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        """
        Identify round number psychological levels
        """
        if round_numbers is None:
            current_price = df['Close'].iloc[-1]
            magnitude = 10 ** int(np.log10(max(current_price, 1)))

            round_numbers = []
            base = int(current_price / magnitude)
            for i in range(base - 2, base + 3):
                round_numbers.extend([i * magnitude, i * magnitude * 2, i * magnitude * 5])

        round_levels = []
        recent_high = df['High'].tail(100).max()
        recent_low = df['Low'].tail(100).min()

        for rn in round_numbers:
            rn_float = float(rn)
            if recent_low <= rn_float <= recent_high:
                round_levels.append({
                    'level': rn_float,
                    'type': 'round_number',
                    'strength': 'major' if rn % 1000 == 0 else 'minor'
                })

        return round_levels

    def apply_role_reversal_rule(self, df: pd.DataFrame, old_resistance: float,
                               breakout_volume_threshold: float = 1.5) -> Dict[str, Any]:
        """
        Apply role reversal rule: broken resistance becomes support
        """
        try:
            breakout_candles = df[df['Close'] > old_resistance]
            if breakout_candles.empty:
                return {'reversed': False, 'new_support': None}

            if 'Volume' not in df.columns:
                return {'reversed': True, 'new_support': old_resistance}

            breakout_volume = breakout_candles['Volume'].max()
            avg_volume = df['Volume'].tail(20).mean()
            
            if pd.isna(avg_volume) or avg_volume == 0:
                return {'reversed': True, 'new_support': old_resistance}

            volume_confirmed = breakout_volume >= avg_volume * breakout_volume_threshold

            if volume_confirmed:
                return {
                    'reversed': True,
                    'new_support': old_resistance,
                    'breakout_volume': float(breakout_volume),
                    'avg_volume': float(avg_volume)
                }

            return {'reversed': False, 'new_support': None}
        except Exception:
            return {'reversed': False, 'new_support': None}

    def apply_expiry_rule(self, df: pd.DataFrame, level: float,
                         max_age_bars: int = 180) -> bool:
        """
        Apply expiry rule: de-prioritize levels not touched recently
        Uses bar count instead of days for robustness
        """
        zone_tolerance = self.touch_tolerance
        zone_high = level * (1 + zone_tolerance)
        zone_low = level * (1 - zone_tolerance)

        touch_mask = ((df['High'] >= zone_low) & (df['High'] <= zone_high)) | \
                     ((df['Low'] >= zone_low) & (df['Low'] <= zone_high))
        
        recent_touches = np.where(touch_mask.tail(200))[0]
        
        if len(recent_touches) == 0:
            return False

        last_touch_relative = recent_touches[-1]
        return last_touch_relative <= max_age_bars

    def find_dynamic_support_resistance(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Find dynamic S&R using moving averages and other indicators
        """
        dynamic_levels = {}

        ma_periods = [20, 50, 100, 200]
        for period in ma_periods:
            if len(df) >= period:
                ma_col = f'MA_{period}'
                df[ma_col] = df['Close'].rolling(window=period).mean()
                dynamic_levels[f'ma_{period}'] = float(df[ma_col].iloc[-1])

        if len(df) >= 50:
            recent_high = df['High'].tail(50).max()
            recent_low = df['Low'].tail(50).min()
            diff = recent_high - recent_low

            fib_levels = [0.236, 0.382, 0.5, 0.618, 0.786]
            for fib in fib_levels:
                level = recent_high - (diff * fib)
                dynamic_levels[f'fib_{int(fib*1000)}'] = float(level)

        return dynamic_levels

    def comprehensive_sr_analysis(self, df: pd.DataFrame, reversal_flag: bool = False) -> Dict[str, Any]:
        """
        Perform comprehensive S&R analysis using all rules
        """
        df = self._validate_df(df).reset_index(drop=True)
        results = {
            'static_levels': [],
            'dynamic_levels': {},
            'round_numbers': [],
            'validated_levels': [],
            'summary': {}
        }

        # 1. Identify peaks and troughs
        peaks, troughs = self.identify_peaks_and_troughs(df)

        # 2. Extract price levels
        peak_prices = df['Close'].iloc[peaks].tolist() if len(peaks) > 0 else []
        trough_prices = df['Close'].iloc[troughs].tolist() if len(troughs) > 0 else []

        # 3. Cluster levels
        support_clusters = self.cluster_levels(trough_prices)
        resistance_clusters = self.cluster_levels(peak_prices)

        # 4. Validate levels
        validated_supports = []
        for cluster in support_clusters:
            if cluster['count'] >= self.min_touches:
                validation = self.validate_level_with_three_touch_rule(df, cluster['avg_price'])
                if validation['is_valid']:
                    vol_val = self.validate_volume_confirmation(df, cluster['avg_price'])
                    level_info = {
                        'level': cluster['avg_price'],
                        'type': 'support',
                        'strength': 'strong' if cluster['count'] >= 5 else 'moderate',
                        'touch_count': cluster['count'],
                        'validation': validation,
                        'volume_confirmed': vol_val['volume_confirmed'],
                        'volume_ratio': vol_val['volume_ratio']
                    }
                    if self.apply_expiry_rule(df, cluster['avg_price']):
                        validated_supports.append(level_info)

        validated_resistances = []
        for cluster in resistance_clusters:
            if cluster['count'] >= self.min_touches:
                validation = self.validate_level_with_three_touch_rule(df, cluster['avg_price'])
                if validation['is_valid']:
                    vol_val = self.validate_volume_confirmation(df, cluster['avg_price'])
                    level_info = {
                        'level': cluster['avg_price'],
                        'type': 'resistance',
                        'strength': 'strong' if cluster['count'] >= 5 else 'moderate',
                        'touch_count': cluster['count'],
                        'validation': validation,
                        'volume_confirmed': vol_val['volume_confirmed'],
                        'volume_ratio': vol_val['volume_ratio']
                    }
                    if self.apply_expiry_rule(df, cluster['avg_price']):
                        validated_resistances.append(level_info)

        # Role reversal
        if reversal_flag:
            reversed_supports = []
            for level in validated_resistances[:]:
                reversal = self.apply_role_reversal_rule(df, level['level'])
                if reversal['reversed']:
                    reversed_supports.append({
                        'level': reversal['new_support'],
                        'type': 'support (reversed)',
                        'strength': 'reversed_resistance',
                        'reversal_info': reversal
                    })
                    validated_resistances.remove(level)
            validated_supports.extend(reversed_supports)

        # Dynamic levels and round numbers
        results['dynamic_levels'] = self.find_dynamic_support_resistance(df)
        results['round_numbers'] = self.identify_round_number_levels(df)
        results['static_levels'] = validated_supports + validated_resistances
        results['validated_levels'] = validated_supports + validated_resistances

        # Summary
        active_levels = results['static_levels']
        results['summary'] = {
            'total_static_levels': len(active_levels),
            'support_levels': len([l for l in active_levels if 'support' in l['type']]),
            'resistance_levels': len([l for l in active_levels if l['type'] == 'resistance']),
            'strong_levels': len([l for l in active_levels if l['strength'] == 'strong']),
            'volume_confirmed_levels': len([l for l in active_levels if l.get('volume_confirmed', False)]),
            'round_numbers_found': len(results['round_numbers'])
        }

        return results

    @staticmethod
    def get_sr_levels(df: pd.DataFrame, touch_tolerance: float = 0.005) -> Dict[str, Any]:
        """
        Convenience function to get S&R levels from dataframe
        """
        analyzer = SupportResistanceAnalyzer(zone_tolerance=touch_tolerance)
        analysis = analyzer.comprehensive_sr_analysis(df)

        supports = [level['level'] for level in analysis['static_levels'] if 'support' in level['type']]
        resistances = [level['level'] for level in analysis['static_levels'] if level['type'] == 'resistance']

        return {
            'supports': sorted(supports),
            'resistances': sorted(resistances),
            'strongest_support': min(supports) if supports else None,
            'strongest_resistance': max(resistances) if resistances else None,
            'analysis': analysis
        }
