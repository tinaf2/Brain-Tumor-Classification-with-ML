# -*- coding: utf-8 -*-
"""Brain Tumor Classification.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/16P9fEqq2IzU_ofk3jje3HpRIXYjygwp9
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

! kaggle datasets download -d masoudnickparvar/brain-tumor-mri-dataset --unzip

def get_class_paths(path):
    classes = []
    class_paths = []

    # Iterate through directories in the training path
    for label in os.listdir(path):
        label_path = os.path.join(path, label)

        # Check if it's a directory
        if os.path.isdir(label_path):
            # Iterate through images in the label directory
            for image in os.listdir(label_path):
                image_path = os.path.join(label_path, image)

                # Add class and path to respective lists
                classes.append(label)
                class_paths.append(image_path)

    # Create a DataFrame with the collected data
    df = pd.DataFrame({
        'Class Path' : class_paths,
        'Class': classes
    })

    return df

tr_df = get_class_paths("/content/Training")

tr_df

ts_df = get_class_paths("/content/Testing")

ts_df

plt.figure(figsize=(15, 7))
ax = sns.countplot(data=tr_df, x=tr_df['Class'])

plt.figure(figsize=(15, 7))
ax = sns.countplot(data=ts_df, x=ts_df['Class'])

from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, Flatten
from tensorflow.keras.optimizers import Adamax
from tensorflow.keras.metrics import Precision, Recall
from tensorflow.keras.preprocessing.image import ImageDataGenerator

valid_df, ts_df = train_test_split(ts_df, train_size=0.5, stratify=ts_df['Class'])

valid_df

ts_df

# Preprocessing the data

batch_size = 32

img_size = (299, 299)

image_generator = ImageDataGenerator(rescale=1/255, brightness_range=(0.8, 1.2))

ts_gen = ImageDataGenerator(rescale=1/255)

tr_gen = image_generator.flow_from_dataframe(tr_df, x_col='Class Path',
                                             y_col='Class',
                                             batch_size=batch_size,
                                             target_size=img_size)

valid_gen = image_generator.flow_from_dataframe(valid_df, x_col='Class Path',
                                             y_col='Class',
                                             batch_size=batch_size,
                                             target_size=img_size)

ts_gen = ts_gen.flow_from_dataframe(ts_df, x_col='Class Path',
                                             y_col='Class',
                                             batch_size=16,
                                             target_size=img_size, shuffle=False)

plt.figure(figsize=(20,20))
for i in range(16):
    plt.subplot(4, 4, i+1)
    batch = next(tr_gen)
    image = batch[0][0]
    label = batch[1][0]
    plt.imshow(image)

    # Get the class index
    class_index = np.argmax(label)

    # Get the list of class names and class indices
    class_names = list(tr_gen.class_indices.keys())
    class_indices = list(tr_gen.class_indices.values())

    # Find the index of the class_index in the list of indices
    index_position = class_indices.index(class_index)

    # Get the class name using the index position
    class_name = class_names[index_position]

    plt.title(f"Class: {class_name}")
    plt.axis('off')

plt.tight_layout()
plt.show()

img_shape = (299, 299, 3)

base_model = tf.keras.applications.Xception(include_top= False,
                                           weights= "imagenet",
                                           input_shape= img_shape,
                                           pooling= 'max')

model = Sequential((
    base_model,
    Flatten(),
    Dropout(rate=0.3),
    Dense(128, activation= 'relu'),
    Dropout(rate= 0.25),
    Dense(4, activation= 'softmax')
))

model.compile(Adamax(learning_rate= 0.001),
              loss= 'categorical_crossentropy',
              metrics= ['accuracy',
              Precision(),
              Recall()])

# Training the model
hist = model.fit(tr_gen, epochs=5, validation_data=valid_gen)

metrics = ['accuracy', 'loss', 'precision', 'recall']
tr_metrics = {m: hist.history[m] for m in metrics}
val_metrics = {m: hist.history[f'val_{m}'] for m in metrics}

# Find best epochs and values
best_epochs = {}
best_values = {}
for m in metrics:
    if m == 'loss':
        idx = np.argmin(val_metrics[m])
    else:
        idx = np.argmax(val_metrics[m])
    best_epochs[m] = idx + 1
    best_values[m] = val_metrics[m][idx]

# Plot metrics
plt.figure(figsize=(20, 12))
plt.style.use('fivethirtyeight')

for i, metric in enumerate(metrics, 1):
    plt.subplot(2, 2, i)
    epochs = range(1, len(tr_metrics[metric]) + 1)

    plt.plot(epochs, tr_metrics[metric], 'r', label=f'Training {metric}')
    plt.plot(epochs, val_metrics[metric], 'g', label=f'Validation {metric}')
    plt.scatter(best_epochs[metric], best_values[metric], s=150, c='blue'),
    plt.scatter(best_epochs[metric], best_values[metric], s=150, c='blue',
                label=f'Best epoch = {best_epochs[metric]}')

    plt.title(f'Training and Validation {metric.title()}')
    plt.xlabel('Epochs')
    plt.ylabel(metric.title())
    plt.legend()
    plt.grid(True)

plt.suptitle('Model Training Metrics Over Epochs', fontsize=16)
plt.show()

# Evaluate the model's performace
train_score = model.evaluate(tr_gen, verbose=1) # test how well model performs on data it has seen before
valid_score = model.evaluate(valid_gen, verbose=1) # test if our model is overfitting or generalizing well
test_score = model.evaluate(ts_gen, verbose=1) # completely new dataset - true measure of model's performance

print(f"Train Accuracy: {train_score[1]*100:.2f}%")
print(f"Train Loss: {train_score[0]:.4f}")
print(f"\n\nValidation Accuracy: {valid_score[1]*100:.2f}%")
print(f"Validation Loss: {valid_score[0]:.4f}%")
print(f"\n\nTest Accuracy: {valid_score[1]*100:.2f}%")
print(f"Test Loss: {valid_score[0]:.4f}%")

preds = model.predict(ts_gen)
y_pred = np.argmax(preds, axis=1)

class_dict = {
    0: 'glioma',
    1: 'meningioma',
    2: 'no_tumor',
    3: 'pituitary'
}

# Then create and display the confusion matrix
cm = confusion_matrix(ts_gen.classes, y_pred)
labels = list(class_dict.keys())
plt.figure(figsize=(10,8))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=labels, yticklabels=labels)
plt.xlabel('Predicted Label')
plt.ylabel('True Label')
plt.title('Confusion Matrix')
plt.show()

from PIL import Image

def predict(img_path: str) -> None:
    # Get class labels
    labels = list(class_dict.keys())

    # Create figure
    plt.figure(figsize=(6,8))

    # Load and preprocess image
    img = Image.open(img_path)
    resized_img = img.resize((299, 299))
    img_array = np.asarray(resized_img)
    img_array = np.expand_dims(img_array, axis=0) / 255.0

    # Get model predictions
    predictions = model.predict(img_array)
    probabilities = list(predictions[0])

    # Get predicted class
    predicted_class_idx = np.argmax(probabilities)
    predicted_class = class_dict[predicted_class_idx]

    # Plot original image
    plt.subplot(2, 1, 1)
    plt.imshow(resized_img)
    plt.title(f"Input MRI Image\nPredicted: {predicted_class}")

    # Plot prediction probabilities
    plt.subplot(2, 1, 2)
    bars = plt.barh(labels, probabilities)
    plt.xlabel("Probability", fontsize=15)
    plt.title("Class Probabilities")

    # Add probability labels to bars
    ax = plt.gca()
    ax.bar_label(bars, fmt="%.2f")

    plt.tight_layout()
    plt.show()

    print(f"\nPredicted tumor type: {predicted_class}")

# Using model to make predictions on different images
predict("/content/Testing/meningioma/Te-meTr_0000.jpg")

predict("/content/Testing/meningioma/Te-meTr_0005.jpg")

predict("/content/Testing/glioma/Te-glTr_0000.jpg")

model.save_weights("exception_model.weights.h5")

# Now train a smaller model (CNN model with fewer convolutional layers than Xception model) from scratch without using transfer learning
# - trying to achieve same accuracy using less memory and computing power

from tensorflow.keras.layers import Conv2D, MaxPooling2D
from tensorflow.keras import regularizers

batch_size = 16 # reduce image size

img_size = (224, 224) # reduce batch size (fewer images processed simultaneously)

# Re-initialize all other variables to account for new batch and image sizes

image_generator = ImageDataGenerator(rescale=1/255, brightness_range=(0.8, 1.2))

ts_gen = ImageDataGenerator(rescale=1/255)

tr_gen = image_generator.flow_from_dataframe(tr_df, x_col='Class Path',
                                             y_col='Class',
                                             batch_size=batch_size,
                                             target_size=img_size)

valid_gen = image_generator.flow_from_dataframe(valid_df, x_col='Class Path',
                                             y_col='Class',
                                             batch_size=batch_size,
                                             target_size=img_size)

ts_gen = ts_gen.flow_from_dataframe(ts_df, x_col='Class Path',
                                             y_col='Class',
                                             batch_size=16,
                                             target_size=img_size, shuffle=False)

# Create a Sequential model (stacking layers on top of each other to build model)

cnn_model = Sequential()

# Convolutional layers (4) - each has a different num of convolutional filters
cnn_model.add(Conv2D(512, (3, 3), padding='same', input_shape=(224, 224, 3), activation='relu'))
cnn_model.add(MaxPooling2D(pool_size=(2, 2)))

cnn_model.add(Conv2D(256, (3, 3), padding='same', activation='relu'))
cnn_model.add(MaxPooling2D(pool_size=(2, 2)))
cnn_model.add(Dropout(0.25)) # randomly turns of some connections to prevent overfitting

cnn_model.add(Conv2D(128, (3, 3), padding='same', activation='relu'))
cnn_model.add(MaxPooling2D(pool_size=(2, 2)))
cnn_model.add(Dropout(0.25))

cnn_model.add(Conv2D(64, (3, 3), padding='same', activation='relu')) # 64 filters to find the highest level features
cnn_model.add(MaxPooling2D(pool_size=(2, 2)))

# Flatten the output for fully connected layers
cnn_model.add(Flatten())

# Fully connected layers
cnn_model.add(Dense(256, activation='relu', kernel_regularizer=regularizers.l2(0.01)))
cnn_model.add(Dropout(0.35))

cnn_model.add(Dense(4, activation='softmax')) # Output layer with 4 layers for the 4 classes

# Compile the model
cnn_model.compile(Adamax(learning_rate= 0.001),
              loss= 'categorical_crossentropy',
              metrics= ['accuracy',
              Precision(name='precision'),
              Recall(name='recall')])

# Display the model summary
cnn_model.summary()

# Now we train the model using same code used for other model
history = cnn_model.fit(tr_gen, epochs=5, validation_data=valid_gen)

metrics = ['accuracy', 'loss', 'precision', 'recall']
tr_metrics = {m: history.history[m] for m in metrics}
val_metrics = {m: history.history[f'val_{m}'] for m in metrics}

# Find best epochs and values
best_epochs = {}
best_values = {}
for m in metrics:
    if m == 'loss':
        idx = np.argmin(val_metrics[m])
    else:
        idx = np.argmax(val_metrics[m])
    best_epochs[m] = idx + 1
    best_values[m] = val_metrics[m][idx]

# Plot metrics
plt.figure(figsize=(20, 12))
plt.style.use('fivethirtyeight')

for i, metric in enumerate(metrics, 1):
    plt.subplot(2, 2, i)
    epochs = range(1, len(tr_metrics[metric]) + 1)

    plt.plot(epochs, tr_metrics[metric], 'r', label=f'Training {metric}')
    plt.plot(epochs, val_metrics[metric], 'g', label=f'Validation {metric}')
    plt.scatter(best_epochs[metric], best_values[metric], s=150, c='blue'),
    plt.scatter(best_epochs[metric], best_values[metric], s=150, c='blue',
                label=f'Best epoch = {best_epochs[metric]}')

    plt.title(f'Training and Validation {metric.title()}')
    plt.xlabel('Epochs')
    plt.ylabel(metric.title())
    plt.legend()
    plt.grid(True)

plt.suptitle('Model Training Metrics Over Epochs', fontsize=16)
plt.show()

# Evaluate the model's performace
train_score = cnn_model.evaluate(tr_gen, verbose=1) # test how well model performs on data it has seen before
valid_score = cnn_model.evaluate(valid_gen, verbose=1) # test if our model is overfitting or generalizing well
test_score = cnn_model.evaluate(ts_gen, verbose=1) # completely new dataset - true measure of model's performance

print(f"Train Accuracy: {train_score[1]*100:.2f}%")
print(f"Train Loss: {train_score[0]:.4f}")
print(f"\n\nValidation Accuracy: {valid_score[1]*100:.2f}%")
print(f"Validation Loss: {valid_score[0]:.4f}%")
print(f"\n\nTest Accuracy: {valid_score[1]*100:.2f}%")
print(f"Test Loss: {valid_score[0]:.4f}%")

preds = cnn_model.predict(ts_gen)
y_pred = np.argmax(preds, axis=1)

class_dict = {
    0: 'glioma',
    1: 'meningioma',
    2: 'no_tumor',
    3: 'pituitary'
}

# Then create and display the confusion matrix
cm = confusion_matrix(ts_gen.classes, y_pred)
labels = list(class_dict.keys())
plt.figure(figsize=(10,8))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=labels, yticklabels=labels)
plt.xlabel('Predicted Label')
plt.ylabel('True Label')
plt.title('Confusion Matrix')
plt.show()

clr = classification_report(ts_gen.classes, y_pred)
print(clr)

cnn_model.save("cnn_model.h5")

"""Part 2: Streamlit Web App"""

! pip install streamlit pyngrok python-dotenv

from threading import Thread
from pyngrok import ngrok
from google.colab import userdata

ngrok_token = userdata.get('NGROK_AUTH_TOKEN')

ngrok.set_auth_token(ngrok_token)

def run_streamlit():
    os.system("streamlit run /content/app.py --server.port 8501")

# Commented out IPython magic to ensure Python compatibility.
# %%writefile app.py
# 
# import streamlit as st
# import tensorflow as tf
# from tensorflow.keras.models import load_model
# from tensorflow.keras.preprocessing import image
# import numpy as np
# import plotly.graph_objects as go
# import cv2
# from tensorflow.keras.models import Sequential
# from tensorflow.keras.layers import Dense, Dropout, Flatten
# from tensorflow.keras.optimizers import Adamax
# from tensorflow.keras.metrics import Precision, Recall
# import google.generativeai as genai
# from google.colab import userdata
# import PIL.Image
# import os
# from google.colab import userdata
# from dotenv import load_dotenv
# load_dotenv()
# 
# 
# genai.configure(api_key=os.getenv("AIzaSyAGl4E431MJAFVXRabpjlzJkD2jSVG5sAM"))
# 
# output_dir = 'saliency_maps'
# os.makedirs(output_dir, exist_ok=True)
# 
# def generate_explanation(img_path, model_prediction, confidence):
# 
#     prompt = f"""You are an expert neurologist. You are tasked with explaining a saliency map of a brain tumor MRI scan
#     as either glioma, meningioma, pituitary, or no tumor.
# 
#     The saliency map highlights the regions of the image that the machine learning model is focusing on to make the prediction.
# 
#     The deep learning model predicted the image to be of class '{model_prediction}' with a confidence of {confidence * 100}%.
# 
#     In your response:
#     - Explain what regions of the brain the model is focusing on, based on the saliency map. Refer to the regions highlighted in light cyan,
#     those are the regions where the model is focusing on.
#     - Explain possible reasons why the model made the prediction it did.
#     - Don't mention anything like 'The saliency map highlights the regions the model is focusing on, which are in light cyan'
#     in your explanation.
#     - Keep your explanation to 4 sentences max.
# 
#     Let's think step by step about htis. Verify step by step.
#     """
# 
#     img = PIL.Image.open(img_path)
# 
#     model = genai.GenerativeModel(model_name="gemini-1.5-flash")
#     response = model.generate_content([prompt, img])
# 
#     return response.text
# 
# def generate_saliency_map(model, img_array, class_index, img_size):
#     with tf.GradientTape() as tape:
#         img_tensor = tf.convert_to_tensor(img_array)
#         tape.watch(img_tensor)
#         predictions = model(img_tensor)
#         target_class = predictions[:, class_index]
# 
#     gradients = tape.gradient(target_class, img_tensor)
#     gradients = tf.math.abs(gradients)
#     gradients = tf.reduce_max(gradients, axis=-1)
#     gradients = gradients.numpy().squeeze()
# 
#     # Resize gradients to match original image size
#     gradients = cv2.resize(gradients, img_size)
# 
#     # Create a circular mask for the brain area
#     center = (gradients.shape[0] // 2, gradients.shape[1] // 2)
#     radius = min(center[0], center[1]) - 10
#     y, x = np.ogrid[:gradients.shape[0], :gradients.shape[1]]
#     mask = (x - center[0])**2 + (y - center[1])**2 <= radius**2
# 
#     # Apply mask to gradients
#     gradients = gradients * mask
# 
#     # Normalize only the brain area
#     brain_gradients = gradients[mask]
#     if brain_gradients.max() > brain_gradients.min():
#         brain_gradients = (brain_gradients - brain_gradients.min()) / (brain_gradients.max() - brain_gradients.min())
#     gradients[mask] = brain_gradients
# 
#     # Apply a higher threshold
#     threshold = np.percentile(gradients[mask], 8)
#     gradients[gradients < threshold] = 0
# 
#     # Apply more aggressive smoothing
#     gradients = cv2.GaussianBlur(gradients, (11, 11), 0)
# 
#     # Create a heatmap overlay with enhanced contrast
#     heatmap = cv2.applyColorMap(np.uint8(255 * gradients), cv2.COLORMAP_JET)
#     heatmap = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)
# 
#     # Resize heatmap to match original image size
#     heatmap = cv2.resize(heatmap, img_size)
# 
#     # Superimpose the heatmap on original image with increased opacity
#     original_img = image.img_to_array(img)
#     superimposed_img = heatmap * 0.7 + original_img * 0.3
#     superimposed_img = superimposed_img.astype(np.uint8)
# 
#     img_path = os.path.join(output_dir, uploaded_file.name)
#     with open(img_path, "wb") as f:
#         f.write(uploaded_file.getbuffer())
# 
#     saliency_map_path = f'saliency_maps/{uploaded_file.name}'
# 
#     # Save the saliency map
#     cv2.imwrite(saliency_map_path, cv2.cvtColor(superimposed_img, cv2.COLOR_RGB2BGR))
# 
#     return superimposed_img
# 
# 
# 
# def load_xception_model(model_path):
#     img_shape=(299,299,3)
#     base_model = tf.keras.applications.Xception(include_top=False, weights="imagenet",
#                                                 input_shape=img_shape, pooling='max')
# 
#     model = Sequential([
#         base_model,
#         Flatten(),
#         Dropout(rate=0.3),
#         Dense(128, activation='relu'),
#         Dropout(rate=0.25),
#         Dense(4, activation='softmax')
#     ])
# 
#     model.build((None,) + img_shape)
# 
#     # Compile the model
#     model.compile(Adamax(learning_rate=0.001),
#                   loss='categorical_crossentropy',
#                   metrics=['accuracy',
#                               Precision(),
#                               Recall()])
# 
#     model.load_weights(model_path)
#     return model
# 
# st.title("Brain Tumor Classification")
# 
# st.write("Upload an image of a brain MRI scan to classify.")
# 
# uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])
# 
# if uploaded_file is not None:
#     selected_model = st.radio(
#         "Select a model:",
#         ("Transfer Learning - Xception", "Custom CNN")
#     )
# 
#     if selected_model == "Transfer Learning - Xception":
#         model = load_xception_model('/content/exception_model.weights.h5')
#         img_size = (299, 299)
#     else:
#         model = load_model('/content/cnn_model.h5')
#         img_size = (224, 224)
# 
#     labels = ['Glioma', 'Meningioma', 'No Tumor', 'Pituitary']
#     img = image.load_img(uploaded_file, target_size=img_size)
#     img_array = image.img_to_array(img)
#     img_array = np.expand_dims(img_array, axis=0)
#     img_array /= 255.0
# 
#     prediction = model.predict(img_array)
# 
#     # Get the class with the highest probability
#     class_index = np.argmax(prediction[0])
#     result = labels[class_index]
# 
#     st.write(f"Predicted Class: {result}")
#     st.write("Predictions:")
#     for label, prob in zip(labels, prediction[0]):
#         st.write(f"{label}: {prob:.4f}")
# 
# 
#     saliency_map = generate_saliency_map(model, img_array, class_index, img_size)
# 
#     col1, col2 = st.columns(2)
#     with col1:
#         st.image(uploaded_file, caption='Uploaded Image', use_column_width=True)
#     with col2:
#         st.image(saliency_map, caption='Saliency Map', use_column_width=True)
# 
#     st.write("## Classification Results")
# 
#     result_container = st.container()
#     result_container = st.container()
#     result_container.markdown(
#         f"""
#         <div style="background-color: #000000; color: #ffffff; padding: 30px; border-radius: 15px;">
#           <div style="display: flex; justify-content: space-between; align-items: center;">
#             <div style="flex-basis: 45%; text-align: center;">
#               <h3 style="color: #ffffff; margin-bottom: 10px; font-size: 20px;">Prediction</h3>
#               <p style="font-size: 36px; font-weight: 800; color: #FF0000; margin: 0;">
#                   {result}
#               </p>
#             </div>
#             <div style="width: 2px; height: 80px; background-color: #ffffff; margin: 0 20px;"></div>
#             <div style="flex-basis: 45%; text-align: center;">
#               <h3 style="color: #ffffff; margin-bottom: 10px; font-size: 20px;">Confidence</h3>
#               <p style="font-size: 36px; font-weight: 800; color: #2196F3; margin: 0;">
#                   {prediction[0][class_index]:.4%}
#               </p>
#             </div>
#           </div>
#         </div>
#         """,
#           unsafe_allow_html=True
#     )
# 
#     # Prepare data for Plotly chart
#     probabilities = prediction[0]
#     sorted_indices = np.argsort(probabilities)[::-1]
#     sorted_probabilities = probabilities[sorted_indices]
#     sorted_labels = [labels[i] for i in sorted_indices]
# 
#     # Create a Plotly bar chart
#     fig = go.Figure(go.Bar(
#         x=sorted_probabilities,
#         y=sorted_labels,
#         orientation='h',
#         marker_color=['red' if label == result else 'blue' for label in sorted_labels]
#     ))
# 
#     # Customize the chart layout
#     fig.update_layout(
#         title='Probabilities for each class',
#         xaxis_title='Probability',
#         yaxis_title='Class',
#         height=400,
#         width=600,
#         yaxis=dict(autorange="reversed")
#     )
# 
#     # Add value labels to the bars
#     for i, prob in enumerate(sorted_probabilities):
#         fig.add_annotation(
#             x=prob,
#             y=i,
#             text=f'{prob:.4f}',
#             showarrow=False,
#             xanchor='left',
#             xshift=5
#         )
# 
#     # Display the Plotly chart
#     st.plotly_chart(fig)
# 
#     saliency_map_path = f'saliency_maps/{uploaded_file.name}'
#     explanation = generate_explanation(saliency_map_path, result, prediction[0][class_index])
# 
#     st.write("## Explanation")
#     st.write(explanation)

from google.colab import drive
drive.mount('/content/drive')

thread = Thread(target=run_streamlit)
thread.start()

public_url = ngrok.connect(addr='8501', proto='http', bind_tls=True)

print("Public URL:", public_url)

tunnels = ngrok.get_tunnels()
for tunnel in tunnels:
  print(f"Closing tunnel: {tunnel.public_url} -> {tunnel.config['addr']}")
  ngrok.disconnect(tunnel.public_url)

# Commented out IPython magic to ensure Python compatibility.
# %%writefile .env
# 
# GOOGLE_API_KEY=AIzaSyAGl4E431MJAFVXRabpjlzJkD2jSVG5sAM

