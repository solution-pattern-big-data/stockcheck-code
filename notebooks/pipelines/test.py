
import kfp.compiler
from kfp import dsl

#
@dsl.component(base_image="image-registry.openshift-image-registry.svc:5000/openshift/python:latest",
               packages_to_install=["yfinance", "scikit-learn", "tensorflow", "tf2onnx", "onnx", "minio"])
def download_data():
    import yfinance as yfin
    from sklearn.preprocessing import MinMaxScaler
    from tensorflow import keras
    from keras.models import Sequential
    from keras.layers import Dense, LSTM, Dropout
    from tf2onnx import convert
    import onnx
    from minio import Minio
    """Calculate the sum of the two arguments."""
    #ticker = os.environ.get('TICKER')
    ticker = 'AAPL'
    df = yfin.download(tickers=ticker, period='6mo')
    dataset = df['Close'].fillna(method='ffill')
    dataset = dataset.values.reshape(-1, 1)
    print(dataset.shape)
    
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaler = scaler.fit(dataset)
    dataset = scaler.transform(dataset)
    
    # generate the input and output sequences
    n_lookback = 60  # length of input sequences (lookback period)
    n_forecast = 30  # length of output sequences (forecast period)

    X = []
    Y = []
    
    for i in range(n_lookback, len(dataset) - n_forecast + 1):
        X.append(dataset[i - n_lookback: i])
        Y.append(dataset[i: i + n_forecast])
        
    X = np.array(X)
    Y = np.array(Y)
    
    # fit the model
    model = Sequential(name="forecast")
    model.add(LSTM(units=50, return_sequences=True, input_shape=(n_lookback, 1)))
    model.add(LSTM(units=50))
    model.add(Dense(n_forecast))
    
    model.compile(loss='mean_squared_error', optimizer='adam')
    model.fit(X, Y, epochs=100, batch_size=32, verbose=0)
    
    # generate the forecasts
    X_ = dataset[- n_lookback:]  # last available input sequence
    X_ = X_.reshape(1, n_lookback, 1)

    Y_ = model.predict(X_).reshape(-1, 1)
    Y_ = scaler.inverse_transform(Y_)
    
    model.save("./forecast.keras")
    onnx_model, _ = tf2onnx.convert.from_keras(model)
    onnx.save(onnx_model, "./forecast.onnx")
    
    client = Minio(
    "minio.stock-predict.svc.cluster.local:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False)
    
    buckets = client.list_buckets()
    for bucket in buckets:
        print(bucket.name, bucket.creation_date)
        
    bucket_name = "models"
    source_file = "./forecast.onnx"
    destination_file = "forecast.onnx"
    client.fput_object(bucket_name, destination_file, source_file)

@dsl.pipeline()
def add_pipeline(ticker: str = 'AAPL'):
    """Pipeline to add values.
    """
    first_add_task = download_data()

if __name__ == "__main__":
    kfp.compiler.Compiler().compile(add_pipeline, package_path=__file__.replace(".py", ".yaml"))