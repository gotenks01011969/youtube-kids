from agents.topic_agent import generate_topic
from agents.idea_agent import generate_idea
from agents.content_agent import generate_content
from agents.script_agent import generate_script
from agents.youtube_agent import generate_metadata
from orchestrator.retry import retry_with_feedback
from video.video_agent import generate_video
from uploader.youtube_uploader import upload_to_youtube
from utils.logger import logger
from utils.memory import record_video
from utils.cleanup import cleanup


def run_pipeline():
    logger.info("🚀 Starting automated YouTube Kids pipeline")

    topic = retry_with_feedback(
        generate_topic,
        name="Topic Agent"
    )
    print("----------------------------------------------------------")
    print("topic: ", topic)
    print("----------------------------------------------------------")

    idea = retry_with_feedback(
        lambda: generate_idea(topic),
        name="Idea Agent"
    )
    print("----------------------------------------------------------")
    print("idea: ", idea)
    print("----------------------------------------------------------")

    content = retry_with_feedback(
        lambda: generate_content(topic, idea),
        name="Content Agent"
    )
    print("----------------------------------------------------------")
    print("content: ", content)
    print("----------------------------------------------------------")

    def script_step():
        script = generate_script(topic, idea, content)
        return script

    script = retry_with_feedback(
        script_step,
        max_retries=4,
        name="Script Agent"
    )
    print("----------------------------------------------------------")
    print("script: ", script)
    print("----------------------------------------------------------") 

    video_path = retry_with_feedback(
        lambda: generate_video(script),
        max_retries=2,
        name="Video Generation"
    )
    print("----------------------------------------------------------")
    print("video: ", video_path)
    print("----------------------------------------------------------")

    metadata = retry_with_feedback(
        lambda: generate_metadata(script),
        name="Youtube Agent"
    )
    print("----------------------------------------------------------")
    print("metadata: ", metadata)
    # upload_to_youtube(video_path, topic["topic"], metadata)
    upload_to_youtube(video_path, topic["topic"], metadata, "private")
    print("Uploaded to Youtube")
    print("----------------------------------------------------------")
    
    record_video(topic["topic"], idea["idea"])
    cleanup(video_path)
    print("----------------------------------------------------------")
    print("Cleanup Done")
    print("----------------------------------------------------------")

    logger.info("✅ Pipeline completed successfully")
