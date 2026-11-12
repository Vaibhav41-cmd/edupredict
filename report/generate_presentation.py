"""Create a polished MCA-521 project presentation (16:9) using verified project metrics."""
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.dml import MSO_THEME_COLOR

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'report'; AS=OUT/'assets'
prs=Presentation(); prs.slide_width= Inches(13.333); prs.slide_height= Inches(7.5)
NAVY=RGBColor(15,23,42); INDIGO=RGBColor(79,70,229); CYAN=RGBColor(6,182,212); WHITE=RGBColor(248,250,252); MUTED=RGBColor(148,163,184); DARK=RGBColor(30,41,59); GREEN=RGBColor(16,185,129); GOLD=RGBColor(245,158,11)

def shape(slide,x,y,w,h,color,round=True):
    sh=slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if round else MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h)); sh.fill.solid(); sh.fill.fore_color.rgb=color; sh.line.fill.background(); return sh

def text(slide,x,y,w,h,txt,size=18,color=DARK,bold=False,font='Aptos',align=PP_ALIGN.LEFT,margin=.04):
    box=slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)); tf=box.text_frame; tf.clear(); tf.word_wrap=True; tf.margin_left=Inches(margin); tf.margin_right=Inches(margin); tf.margin_top=Inches(margin); tf.margin_bottom=Inches(margin)
    for i,line in enumerate(txt.split('\n')):
        p=tf.paragraphs[0] if i==0 else tf.add_paragraph(); p.text=line; p.alignment=align; p.font.name=font; p.font.size=Pt(size); p.font.bold=bold; p.font.color.rgb=color; p.space_after=Pt(6)
    return box

def new_slide(title=None,section='MCA-521 · RESEARCH PROJECT'):
    s=prs.slides.add_slide(prs.slide_layouts[6]); s.background.fill.solid(); s.background.fill.fore_color.rgb=WHITE
    shape(s,0,0,13.333,.12,INDIGO,False)
    if title:
        text(s,.62,.35,11.8,.5,title,25,NAVY,True)
        text(s,.65,.95,11,.25,section.upper(),9,INDIGO,True)
        shape(s,.65,1.26,12.0,.02,RGBColor(226,232,240),False)
    n=len(prs.slides); text(s,.68,7.16,8,.18,'KBCNMU JALGAON  •  MASTER OF COMPUTER APPLICATIONS  •  SEMESTER III',8,MUTED,True); text(s,12.1,7.12,.55,.22,f'{n:02d}',9,MUTED,True,align=PP_ALIGN.RIGHT)
    return s

def card(s,x,y,w,h,title,body,accent=INDIGO):
    shape(s,x,y,w,h,RGBColor(255,255,255)); s.shapes[-1].line.color.rgb=RGBColor(226,232,240); shape(s,x,y,.08,h,accent,False)
    text(s,x+.22,y+.16,w-.4,.42,title,16,NAVY,True); text(s,x+.22,y+.68,w-.4,h-.82,body,12,DARK)

def bullets(s,x,y,w,items,size=16,color=DARK,spacing=.52):
    for i,item in enumerate(items):
        shape(s,x,y+i*spacing+.08,.12,.12,INDIGO,True); text(s,x+.28,y+i*spacing,w-.32,spacing,item,size,color)

def picture(s,path,x,y,w,h=None):
    if h: s.shapes.add_picture(str(path), Inches(x), Inches(y), width= Inches(w), height= Inches(h))
    else: s.shapes.add_picture(str(path), Inches(x), Inches(y), width= Inches(w))

# 1 cover
s=prs.slides.add_slide(prs.slide_layouts[6]); s.background.fill.solid(); s.background.fill.fore_color.rgb=NAVY
shape(s,8.45,0,4.9,7.5,RGBColor(30,41,72),False); shape(s,8.45,0,.12,7.5,INDIGO,False)
text(s,.8,.55,7.1,.35,'KAVAYITRI BAHINABAI CHAUDHARI NORTH MAHARASHTRA UNIVERSITY, JALGAON',10,RGBColor(199,210,254),True)
text(s,.82,1.22,7.0,.35,'FACULTY OF SCIENCE AND TECHNOLOGY  |  MCA',12,CYAN,True)
text(s,.82,1.62,7.2,.32,"S.S.V.P. SANSTHA’S  ·  LATE KARMAVEER DR. P. R. GHOGREY SCIENCE COLLEGE, DHULE",10,RGBColor(203,213,225),True)
text(s,.82,2.05,7.2,1.5,'EduPredict',42,WHITE,True); text(s,.86,3.28,7.1,1.1,'STUDENT PASS / FAIL\nPREDICTION SYSTEM',24,WHITE,True)
text(s,.86,4.68,7.0,.8,'Machine learning for academic early-warning support',18,RGBColor(203,213,225))
text(s,.86,5.82,6.9,.75,'MCA-521: Research Project  •  Semester III\nW.E.F. 2024–25  |  Research prototype & working demo',13,RGBColor(199,210,254),True)
s.shapes.add_picture(str(AS/'college_logo.jpg'), Inches(9.15), Inches(.28), width=Inches(3.25))
shape(s,9.0,2.5,3.45,3.85,RGBColor(15,23,42)); text(s,9.4,2.78,2.65,.35,'MODEL SNAPSHOT',12,CYAN,True)
text(s,9.4,3.2,2.7,.62,'0.9082',30,WHITE,True); text(s,9.4,3.8,2.6,.32,'ROC–AUC',12,MUTED)
text(s,9.4,4.18,2.7,.62,'83.50%',26,WHITE,True); text(s,9.4,4.8,2.6,.32,'Logistic Regression accuracy',10,MUTED)
text(s,9.4,5.35,2.7,.5,'2,000 records  •  4 models',11,RGBColor(199,210,254),True)
text(s,.86,6.9,6,.24,'Presenter(s): ____________________     Guide: ____________________',9,MUTED)

# 2 agenda/problem
s=new_slide('Research problem & motivation','01  •  PROBLEM IDENTIFICATION')
card(s,.75,1.65,5.7,2.0,'The practical challenge','Student marks, attendance, assignments and backlog signals are often reviewed in separate records. At-risk patterns can be recognized late, limiting time for support.',INDIGO)
card(s,6.75,1.65,5.75,2.0,'Research question','Can a supervised classification workflow combine common academic and engagement indicators into a repeatable early-warning estimate that staff can inspect and act on?',CYAN)
text(s,.9,4.15,11.5,.4,'Research gap addressed by this prototype',18,NAVY,True)
bullets(s,1.0,4.72,11.3,['Model notebooks often stop at evaluation; this project connects inference to a usable, auditable web workflow.','Prediction is presented with probabilities and context—not as an automatic grade or disciplinary decision.','Focus: lightweight deployment, multiple-model comparison, student-facing access and transparent limitations.'],15)

# 3 objectives/scope
s=new_slide('Objectives, scope & course outcomes','02  •  RESEARCH DESIGN')
card(s,.72,1.58,5.85,4.9,'Project objectives','1  Build a repeatable PASS/FAIL classification pipeline.\n\n2  Compare four estimators using held-out and cross-validation metrics.\n\n3  Persist student profiles and versioned prediction logs.\n\n4  Deliver an administrator dashboard and student portal.\n\n5  Provide a runnable SQLite demo and reproducible test suite.',INDIGO)
card(s,6.78,1.58,5.85,4.9,'MCA-521 learning alignment','CO1 — define a real-world problem: early identification of academic risk.\n\nCO2 — analyze literature and state the implementation gap.\n\nCO3 — apply a stratified evaluation methodology.\n\nCO4 — create a working Flask + ML prototype.\n\nCO5 — evaluate and communicate results responsibly.',CYAN)

# 4 literature
s=new_slide('Literature review & research gap','03  •  LITERATURE AND CONTEXT')
card(s,.75,1.58,3.8,2.0,'Educational data mining','Prior work studies student outcomes from educational records; data quality, validation and interpretation are central.',INDIGO)
card(s,4.78,1.58,3.8,2.0,'Model evaluation','Class imbalance means accuracy alone is incomplete. Precision, recall, F1, ROC-AUC and confusion matrices offer complementary views.',CYAN)
card(s,8.8,1.58,3.8,2.0,'Identified gap','A small, deployable prototype should connect measured models to access-controlled workflows, logs and human-readable guidance.',GREEN)
text(s,.9,4.02,11.3,.4,'Selected sources',17,NAVY,True)
bullets(s,1.0,4.55,11.2,['Romero & Ventura (2010), Educational data mining: a review of the state of the art.','Baker & Inventado (2014), Educational data mining and learning analytics.','Breiman (2001), Random Forests; Han, Kamber & Pei (2012), Data Mining: Concepts and Techniques.','Scikit-learn model evaluation and preprocessing documentation; Flask documentation.'],13)

# 5 methodology
s=new_slide('Research methodology & dataset','04  •  METHOD')
for x,number,title_,body_,accent in [(0.75,'01','Dataset','2,000 labelled records\n11 numeric predictors\nPASS 1,343 · FAIL 657',INDIGO),(3.85,'02','Split & scaling','Stratified 80:20\n1,600 train / 400 test\nStandardScaler',CYAN),(6.95,'03','Model comparison','Logistic Regression\nRBF SVM · Gradient Boosting\nRandom Forest',GREEN),(10.05,'04','Evaluation','Accuracy · Precision\nRecall · F1 · ROC-AUC\n5-fold CV',GOLD)]:
    shape(s,x,2.0,2.55,3.4,RGBColor(255,255,255)); s.shapes[-1].line.color.rgb=RGBColor(226,232,240); text(s,x+.2,2.28,2.1,.45,number,24,accent,True); text(s,x+.2,2.95,2.15,.45,title_,17,NAVY,True); text(s,x+.2,3.65,2.15,1.25,body_,13,DARK)
    if x<10: text(s,x+2.65,3.1,.42,.4,'›',24,MUTED,True,align=PP_ALIGN.CENTER)
text(s,.9,5.9,11.7,.65,'Feature set: five subject marks, internal marks, attendance, study hours, assignment completion, prior backlogs, and derived average marks.',14,DARK)

# 6 architecture flow
s=new_slide('System architecture & prediction workflow','05  •  SYSTEM DESIGN')
picture(s,AS/'system_architecture.png',.72,1.45,6.15,4.95)
picture(s,AS/'prediction_flow.png',7.1,1.45,5.5,4.95)
text(s,.86,6.48,5.8,.3,'Figure: Application components',10,MUTED,False,align=PP_ALIGN.CENTER); text(s,7.15,6.48,5.4,.3,'Figure: Inference flow',10,MUTED,False,align=PP_ALIGN.CENTER)

# 7 system features / design
s=new_slide('Prototype modules & data design','06  •  IMPLEMENTATION')
card(s,.75,1.55,5.65,2.0,'Application modules','Flask routes + templates · SQLAlchemy ORM · MLService · authentication and CSRF · student management · analytics · chatbot · report endpoints.',INDIGO)
card(s,6.75,1.55,5.75,2.0,'Demo delivery','SQLite zero-setup launcher · 30 example profiles · actual saved-model inference · PASS / at-risk student access · interactive feature sliders and presets.',CYAN)
picture(s,AS/'data_model.png',3.25,3.85,6.9,2.65)
text(s,.85,6.55,11.7,.32,'Four entities: Admin, Student, StudentAuth (1:1 with Student), PredictionLog (1:many with Student).',12,MUTED,False,align=PP_ALIGN.CENTER)

# 8 UI demo screenshot
s=new_slide('Working demo: interactive predictor','07  •  PROTOTYPE')
picture(s,AS/'demo_output_screenshot.png',.85,1.45,8.25,4.8)
card(s,9.35,1.68,3.25,1.3,'Try it live','Open `/demo/` to change sliders or choose a profile preset.',INDIGO)
card(s,9.35,3.2,3.25,1.3,'Quick access','Admin dashboard and student PASS / at-risk portals are available in Demo Mode.',CYAN)
card(s,9.35,4.72,3.25,1.3,'Important note','The output is a model estimate for support; it does not guarantee a result.',GOLD)
text(s,1.0,6.45,8,.3,'Figure: illustrative high-resolution interface view; live page performs real inference.',10,MUTED,False,align=PP_ALIGN.CENTER)

# 9 results
s=new_slide('Evaluation results & observations','08  •  RESULTS')
picture(s,AS/'model_metrics.png',.65,1.45,7.25,4.6)
card(s,8.2,1.55,4.4,1.15,'Selected by ROC-AUC','Logistic Regression · 0.9082',INDIGO)
card(s,8.2,2.92,4.4,1.15,'Best observed accuracy','RBF SVM · 84.75%',CYAN)
card(s,8.2,4.29,4.4,1.15,'Logistic Regression','83.50% accuracy · 88.00% F1',GREEN)
text(s,.85,6.27,11.6,.55,'Held-out Logistic Regression confusion matrix (400): TP 242 · TN 92 · FP 39 · FN 27. FAIL recall = 70.23%; missed risk remains a concern.',12,DARK,True)

# 10 tests and implementation
s=new_slide('Implementation, testing & reproducibility','09  •  VERIFICATION')
card(s,.78,1.65,3.75,3.7,'Verified functionality','Live Flask demo on port 5000\n\nReal-time JSON inference\n\nAdmin and student portal routes\n\nDemo seed/reset workflow',INDIGO)
card(s,4.78,1.65,3.75,3.7,'Automated tests','39 tests passed\n\nML pipeline and validators\n\nDemo route integration\n\nStudent login & key pages',CYAN)
card(s,8.78,1.65,3.75,3.7,'Reproduce locally','Install requirements\n\nRun: `python demo.py`\n\nVisit: `/demo/`\n\nSeeded accounts are demo-only; change credentials before real use.',GREEN)
text(s,.92,5.85,11.6,.5,'Environment: Python 3.11 · Flask · scikit-learn · SQLite demo / MySQL configuration · pytest.',14,DARK,True)

# 11 limitations ethics
s=new_slide('Research ethics, limitations & risk','10  •  RESPONSIBLE USE')
bullets(s,.95,1.65,11.3,['Dataset-specific evidence: evaluation is based on one dataset and one held-out split; no external institution validation is claimed.','Class imbalance and threshold choice matter: at-risk recall is not perfect, so some students may not be flagged.','Predictions are not causal explanations, official grades, or guarantees; humans must review context before support decisions.','Use de-identified, consented data; restrict access; define retention and correction procedures; assess subgroup error before deployment.','Demo profiles and credentials are illustrative and must never be treated as real student records.'],16,spacing=.88)

# 12 future / conclusion
s=new_slide('Conclusion & future research','11  •  FINDINGS AND NEXT STEPS')
card(s,.78,1.65,5.6,3.85,'Conclusion','EduPredict connects academic indicators, a comparative ML workflow, stored prediction history and accessible web views. The working demo makes the end-to-end system inspectable without requiring MySQL.',INDIGO)
card(s,6.78,1.65,5.75,3.85,'Future work','External and longitudinal validation · probability calibration · threshold tuning for early-risk sensitivity · fairness analysis · institutional SSO · privacy governance · controlled intervention study.',CYAN)
text(s,.92,5.9,11.4,.45,'Key takeaway: a useful early-warning prototype must pair predictive performance with validation, transparency and responsible human action.',15,NAVY,True,align=PP_ALIGN.CENTER)

# 13 references
s=new_slide('References & discussion','12  •  SOURCES')
refs=['Romero, C. & Ventura, S. (2010). Educational data mining: a review of the state of the art. IEEE TSMC-C, 40(6), 601–618.','Baker, R.S.J.d. & Inventado, P.S. (2014). Educational data mining and learning analytics. In Learning Analytics, Springer.','Breiman, L. (2001). Random Forests. Machine Learning, 45, 5–32.','Han, J., Kamber, M. & Pei, J. (2012). Data Mining: Concepts and Techniques, 3rd ed. Morgan Kaufmann.','Scikit-learn documentation: model evaluation and StandardScaler. https://scikit-learn.org/','Flask documentation. https://flask.palletsprojects.com/','Project repository: https://github.com/Vaibhav41-cmd/edupredict']
bullets(s,.95,1.55,11.5,refs,12,spacing=.58)
text(s,1.2,6.1,10.9,.5,'Thank you  •  Questions & discussion',24,INDIGO,True,align=PP_ALIGN.CENTER)

path=OUT/'EduPredict_MCA521_Presentation.pptx'; prs.save(path); print(f'Created {path} ({path.stat().st_size:,} bytes, {len(prs.slides)} slides)')
