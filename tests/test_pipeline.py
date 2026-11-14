"""Offline regression checks for parsing, retry safety, and scraper cleanup."""

import unittest
from unittest.mock import patch

from DataProcess import processGames
from DataStorage import insertData
from ScrapChessData import scrapChessData
from StockFishReview import stockfishDataProcess

PGN = '''[White "Alice"]
[Black "Bob"]
[Date "2025.10.03"]
[Link "https://www.chess.com/game/live/example"]
[Result "*"]

1. e4 e5 2. Nf3 Nc6 *'''
TIMED = PGN.replace('1. e4 e5 2. Nf3 Nc6 *',
    '1. e4 {[%timestamp 10]} e5 {[%timestamp 20]} 2. Nf3 {[%timestamp 30]} Nc6 {[%timestamp 40]} *')


class PipelineTests(unittest.TestCase):
    @patch('DataProcess.stockfishDataProcess', return_value={})
    def test_timestamps_and_stable_per_player_identity(self, analyze):
        raw = PGN + '\n ***TimeStamp*** \n' + TIMED
        white = processGames('Alice', raw)
        black = processGames('Bob', raw)
        self.assertEqual(white['TimePerMove'], [1, 3])
        self.assertEqual(black['TimePerMove'], [2, 4])
        self.assertEqual(white['game_id'], processGames('ALICE', raw)['game_id'])
        self.assertNotEqual(white['game_id'], black['game_id'])
        analyze.assert_called()

    @patch('DataProcess.stockfishDataProcess', return_value={'summary': {'total_moves': 2}})
    def test_missing_timestamps_still_analyzes_and_rejects_wrong_player(self, _):
        game = processGames('Alice', PGN)
        self.assertEqual(game['summary']['total_moves'], 2)
        self.assertEqual(game['AverageTimePerMove'], 0)
        self.assertEqual(processGames('Alice', ''), {})
        with self.assertRaises(ValueError):
            processGames('Other', PGN)

    @patch('DataProcess.stockfishDataProcess', return_value={})
    def test_custom_starting_position_is_preserved(self, _):
        raw = '[White "Alice"]\n[Black "Bob"]\n[SetUp "1"]\n[FEN "8/8/8/8/8/8/1k6/7K b - - 0 1"]\n\n1... Kc2 *'
        self.assertIn('[FEN ', processGames('Bob', raw)['Pgn'])

    @patch('DataStorage.MongoClient')
    def test_retry_upserts_and_empty_input_has_no_writes(self, client):
        self.assertEqual(insertData('Alice', {}), 'no data')
        client.assert_not_called()
        data = {
            'game_id': 'stable-id', 'Date': '2025.10.03', 'UserColor': 'White',
            'summary': {'total_moves': 0, 'blunder': 0, 'mistake': 0, 'inaccuracy': 0},
            'centipawnLoseList': [], 'AverageTimePerMove': 0, 'accuracy': None,
            'opening': 'Unknown', 'Result': '*',
        }
        insertData('Alice', data)
        insertData('Alice', data)
        db = client.return_value.__enter__.return_value.__getitem__.return_value
        for call in db.games.update_one.call_args_list:
            self.assertEqual(call.args[0], {'game_id': 'stable-id'})
            self.assertTrue(call.kwargs['upsert'])
        self.assertEqual(db.games.update_one.call_count, 2)
        db.games.insert_one.assert_not_called()
        self.assertEqual(db.stats.update_one.call_count, 2)

    @patch('ScrapChessData.webdriver.Chrome')
    def test_failed_navigation_closes_browser_and_propagates(self, chrome):
        chrome.return_value.get.side_effect = RuntimeError('navigation failed')
        with patch('ScrapChessData.Service'), patch.dict('os.environ', {'SCRAPE_AFTER_DATE': ''}):
            with self.assertRaisesRegex(RuntimeError, 'navigation failed'):
                scrapChessData('Alice')
        chrome.return_value.quit.assert_called_once()

    @patch('StockFishReview.find_opening', return_value='Unknown')
    @patch('StockFishReview.analyze_pgn_with_stockfish')
    def test_black_mistake_is_classified_from_black_perspective(self, analyze, _):
        analyze.return_value = [
            {'eval_before': 0, 'eval_after': 0, 'phase': 'Opening'},
            {'eval_before': 0, 'eval_after': 400, 'phase': 'Endgame'},
        ]
        result = stockfishDataProcess(PGN, 'black')
        self.assertEqual(result['summary']['blunder'], 1)
        self.assertEqual(result['centipawnLoseList'], [400])
        self.assertIsNotNone(result['phases']['Endgame'])
        self.assertGreaterEqual(result['accuracy'], 0)


if __name__ == '__main__':
    unittest.main()
