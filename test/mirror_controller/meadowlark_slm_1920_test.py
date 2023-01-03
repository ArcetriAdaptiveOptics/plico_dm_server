import unittest
import numpy as np

from plico_dm_server.controller.meadowlark_slm_1920 import \
MeadowlarkSlm1920, MeadowlarkError
from plico_dm_server.controller.fake_meadowlark_slm_1920 import \
FakeSlmLib, FakeImageLib

class MeadowlarkSlm1920Test(unittest.TestCase):

    LUT_FILE_NAME = "C:\\Users\\labot\\Desktop\\SLM\\slm6208_at635_PCIe.LUT"
    WFC_FILE_NAME = "C:\\Users\\labot\\Desktop\\SLM\\slm6208_at635_WFC.bmp"
    WAVELEGTH_CALIBRATION = 635e-9  # meters
    MEAN_TEMPERATURE = 25.2 # celsius

    def setUp(self):

        self._slm_lib = FakeSlmLib()
        self._image_lib = FakeImageLib()
        self._dm = MeadowlarkSlm1920(
            self._slm_lib, self._image_lib, self.LUT_FILE_NAME, self.WFC_FILE_NAME, self.WAVELEGTH_CALIBRATION)

    def tearDown(self):
        self._dm.deinitialize()

    def testGetNumberOfActuators(self):
        Nact = self._slm_lib.HEIGHT * self._slm_lib.WIDTH
        self.assertEqual(
            Nact,
            self._dm.getNumberOfActuators())
        
    def testGetHeightAndWidthInPixels(self):
        width = self._slm_lib.WIDTH
        height = self._slm_lib.HEIGHT
        self.assertEqual(
            width, self._dm.getWidthInPixels())
        self.assertEqual(
            height, self._dm.getHeightInPixels())
        
    def testSerialNumber(self):
        serial_number = self._slm_lib.VALID_SERIAL_NUMBER
        self.assertEqual(
            serial_number, self._dm.serialNumber())
        
    def testGetTemperatureInCelsius(self):
        self.assertEqual(self.MEAN_TEMPERATURE,\
                         self._dm.getTemperatureInCelsius())
    
    def testModulo256Conversion(self): 
        input_data = np.array([0, 0.2, 0.7, \
                               1, 1.2, 1.9, \
                               254, 254.2, 254.9, \
                               255, 255.3, 256, 257, 258])
        expected_data = np.array([0, 0, 1, \
                                  1, 1, 2, \
                                  254, 254, 255, \
                                  255, 255, 0, 1, 2], dtype = np.uint8)
        output_data = self._dm._convert2_modulo256(array = input_data, norm = 255)
        
        self.assertEqual(expected_data.tolist(), output_data.tolist())
        
    def testWriteImageWithWrongInputArray(self):
        input_image  = np.linspace(-1., 1.5, 10)
        self.assertRaises(
            MeadowlarkError, self._dm._write_image, input_image)
    
        

if __name__ == "__main__":
    unittest.main()
