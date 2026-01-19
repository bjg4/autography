---
title: "Untitled"
author: Teresa Torres
source_type: book_chapter
book_title: "Continuous Discovery Habits"
chapter_number: 19
scraped_date: '2026-01-19'
---

CHAPTER ELEVEN

MEASURING IMPACT

“Your delusions, no matter how convincing, will wither under the harsh light of data.”

— Alistair Croll and Benjamin Yoskovitz, Lean Analytics

I was excited to join AfterCollege as their Vice President of Product and Design. AfterCollege helps new college graduates find their first job out of school. I had experience in the recruiting industry, but little experience with this particular customer segment, so I kicked off my continuous-interviewing habit during the first week on the job.

Right away, I learned something surprising. I asked college seniors to tell me about their experience looking for a job. Most expressed the same sentiment over and over again. The vast majority of job boards (including ours) asked students two questions: 1) What type of job do you want? 2) In what location? Unfortunately, most of the students that I talked to didn’t know how to answer either of these questions. They had no idea what types of jobs they were qualified for, and they were open to living in many places. The average 22-year-old doesn’t have enough work experience to even be aware of what types of jobs exist, and they have the location flexibility to go where the best opportunities are. Some had a preference to return home or to stay near their college town, but about half were willing to go anywhere. It didn’t take long for me to realize this was a huge problem. We had to stop asking college students questions they couldn’t answer.

As a product team, we realized that we had proprietary data that could help us solve this problem. We had years of behavioral data about which types of jobs students applied to, and, more importantly, we knew from working with employers what types of students they wanted for different types of jobs. In other words, we were in a great position to tell students what types of jobs they were qualified for if they told us what they studied.

Instead of asking, “What type of job do you want?” and “Where do you want to work?” we realized we could ask students, “Where do you go to school?” “What are you studying?” and “When do you plan to graduate?” We suspected these questions would be much easier for students to answer, and we thought we could use their answers to recommend jobs to them.

Our long-term vision was to develop a machine-learning algorithm that matched students to the best jobs based on their own preferences and what we knew employers wanted. But before we invested in a machine-learning algorithm (we didn’t know anything about machine learning yet), we needed to learn if this idea was worth investing in. It was so different from what everyone else was doing, we needed to make sure it would work.

To build a quick prototype, we realized that, as working professionals, we had more experience with job types than most college seniors and that we could create a crude approximation of our matching algorithm by creating saved searches for each of the areas of study in our system. Instead of having a sophisticated machine-learning algorithm behind the scenes, we simply crafted search queries ourselves. For example, if a student indicated they were an English major, we might search for marketing, content management, journalism, speech writing, and public-relations jobs. It wouldn’t be perfect, but we thought it would be better than what students were entering themselves.

We also knew it would help us quickly evaluate how successful our new idea might be. We had dozens of assumptions we wanted to test. Would college students trust our recommendations? Would they be open to exploring jobs they themselves didn’t select? Would they be confused by our unique interface? After all, every other job board asked them to enter what type of job they wanted. Could we collect enough feedback to continue to refine our algorithm? Would our metrics show that this solution was better than what we currently had?

We knew we wanted to start small, as this idea was full of risk. So, we started by diverting a small percentage of our traffic to a new search page. Students entered their area of study, and we ran the relevant “saved search” behind the scenes. We were able to get this working prototype live in just a few days. We then watched what happened.

In our traditional “What type of job do you want?” interface, only 36% of students started a search. Two thirds of our site visitors never even started their job search. With our new “Tell us what you studied” interface, 83% of our visitors started their search. This was a huge improvement. Our new questions were much easier to answer, so more students were able to start their search.

But what happened after that? We found that students who entered job types and locations were more likely to view and apply for jobs, but not by much (only about 10%). We suspected it was because these students already had an inkling of what they wanted to do and where they wanted to work. But for everyone else, that interface simply didn’t work. In our new interface, we saw a small drop-off in the number of searchers who viewed and applied for jobs, but we saw many more students start their search, so our overall performance was much better in the new interface. We knew right away it was safe to keep investing in this idea.

But where should we go from here? We didn’t have a production-quality product. Remember, we tested with a crude prototype that we cobbled together in just a few days. We still had many more assumptions to test. We didn’t feel like we were done with discovery. But we also were seeing better results with our prototype than we were with our production-quality product.

We debated about whether we should switch all of our traffic to the new prototype. We were seeing great results from our early assumptions tests, but we still had one key question to answer: Did our new idea drive our desired outcome? Our desired outcome wasn’t to increase search starts, nor was it to increase job views or job applications. It was to increase the number of students getting jobs through our platform. We thought if we could get more students starting their search, we would increase the number of students who found jobs on our platform. But job views and applications aren’t always leading indicators of hires. A student can view and apply to many jobs and never hear back from an employer. We needed to make sure that students were as likely (and hopefully, more likely) to find a job with our new interface as they were with our old interface. We decided we needed to continue to split our traffic until we could confirm that our new interface supported our desired outcome.

This story illustrates a few key lessons. First, it’s easy to get caught up in successful assumption tests. The world is full of good ideas that will succeed on some level. However, an outcome-focused product trio needs to stay focused on the end goal—driving the desired outcome. We need to remember to measure not just what we need to evaluate our assumption tests, but also what we need to measure impact on our outcome.

Second, this story also highlights the iterative nature of discovery and delivery. Many teams ask, “When are we done with discovery? When do we get to send our ideas to delivery?” The answer to the first question is simple. You are never done with discovery. Remember, this book is about continuous discovery. There is always more to learn and to discover. The second question is harder to answer. In the AfterCollege story, we had already started the delivery work. Our prototype had a working interface that real customers could use. We were collecting real data. Our discovery required that we start delivery. Measuring the impact of that delivery resulted in us needing to do more discovery.

This is why we say discovery feeds delivery and delivery feeds discovery. They aren’t two distinct phases. You can’t have one without the other. In Chapter 10, you learned to iteratively invest in experiments, to start small, and to grow your investment over time. Inevitably, as your experiments grow, you are going to need to test with a real audience, in a real context, with real data. Testing in your production environment is a natural progression for your discovery work. It’s also where your delivery work begins. If you instrument your delivery work, discovery will not only feed delivery, but delivery will feed discovery.

In this chapter, you’ll learn how to instrument your product so that you can evaluate assumption tests using live prototypes. You’ll learn how to measure the impact of your delivery work, using your desired outcome as your North Star. And you’ll learn how to keep your discovery and delivery tightly coupled so that you never have to wonder if you are ready for delivery.

Don’t Measure Everything

It’s counterintuitive, but when instrumenting your product, don’t try to measure everything from the start. You’ll quickly get overwhelmed. You’ll spend weeks debating what events to track, how to name your events, and who is responsible for what before you even get started. This is a waste of time. There is no way to know from the outset how you should set everything up. No matter how much planning you do, you’ll make mistakes. You’ll measure something that you thought meant one thing and discover later that it really meant something else. You’ll develop a naming schema only to later discover that you forgot about a key part of the product. You’ll find the perfect way to measure a key action only to learn months later that you had a bug that caused that event to trigger ten times more often than it should have. It happens to all of us. Trust that you’ll learn as you go.

Instead of trying to plan everything upfront, start small, and experiment your way to the best instrumentation.

Instrument Your Evaluation Criteria

Start by instrumenting what you need to collect to evaluate your assumption tests. As you build your live prototypes54, consider what you need to measure to support your evaluation criteria. Don’t worry about measuring too much beyond that. For example, in the story that opens this chapter, we had several assumptions we needed to test:

- Students will start more searches if we ask them easier questions.
- Students will view jobs that we recommend.
- Students will apply to jobs that we recommend.

We defined evaluation criteria for each assumption:

- 250 out of 500 visitors will start their search using our new interface. (Remember, we were seeing only 180 out of 500, or 36%, start their search on our old interface. We wanted to see a big jump in search starts to warrant such a different interface.)
- At least 63 of our 500 students will view at least one job. (Our current interface was performing at 81 out of 500. We set our initial criteria lower, because we knew our canned searches weren’t perfect, and we were confident we could improve them over time.)
- At least 7 of our 500 students would apply for a job. (Our current interface was performing at 12 out of 500. Again, we set our initial criteria lower because we knew our results would get better over time.)

With this evaluation criteria in mind, here’s what we measured:

- # of people who visited the search start page
- # of people who started a search
- # of people who viewed at least one job
- # of people who applied for at least one job

Notice how we are counting the number of people who took a specific action and not counting the number of actions. This is an important distinction to pay attention to when instrumenting your product. Sometimes you’ll want to count people. Other times you’ll want to count actions. A good way to suss this out is to ask, “If one person did many actions, does that create as much value as many people doing one action?” If you need many people to take action, you’ll want to count people. If it doesn’t matter how many people take action, you’ll want to count actions.

In this case, our assumptions were more about the perception of our new interface. We were concerned that students might not trust our recommendations. So, we wanted to measure how many people engaged with our job listings. We wanted to make sure that the new interface was working for more people than the old interface.

However, when we started to measure the relevance of our saved searches, we started to count actions. We wanted to know how many jobs people found to be compelling. This wasn’t a straightforward metric. If someone views 25 jobs, it might be because they are finding 25 jobs that interest them. Or it might be because it took 25 tries before a job interested them. For relevance, we took two measurements. We measured the position of a job view in the search result (e.g., a student viewed the first vs. third job in the search results). We also measured the ratio of job views to job applications (e.g., the number of jobs someone had to view before they applied for a job).

Counting people helped us understand how many of our students were having success on our platform. Counting actions helped us understand how hard each student had to work to find success.

Notice, however, that we did not start by measuring everything. We didn’t track every click on every page. We started with our assumptions, and we measured exactly what we needed to test our assumptions.

Measure Impact on Your Desired Outcome

In addition to instrumenting what you need to evaluate your assumption tests, you also want to measure what you need to evaluate your progress toward your desired outcome. Our outcome at AfterCollege was to increase the number of students who found jobs on our platform. For our assumption tests, we were measuring search starts, job views, and job applications, but these metrics were only leading indicators of our desired outcome.

Over time, we also wanted to move closer to measuring our outcome itself, so that we could track progress week over week and quarter over quarter. When I started at AfterCollege, we didn’t have a way of measuring how often a student got a job. We lost track of students after they applied for a job. The post-apply steps like interviewing, receiving an offer, and accepting an offer all happened off of our platform. We needed to find a way to incentivize students to tell us when they got a job or employers to tell us when they made a hire.

Some people in the company argued that we should measure our success by job applications. After all, we had no control over who a company hired or how a student interviewed. But the number of job applications was an easy metric to game. It would be easy to encourage students to apply to many jobs, but this wouldn’t necessarily increase their success of finding a job. If we wanted to measure the value we created for our customers, we knew we needed to measure when a student got a job. We couldn’t be afraid to measure hard things.

Since most college students have little to no interviewing experience, nor do they know how to negotiate offers, we decided that we could use this lack of knowledge to help us measure what happens after they completed an application. Twenty-one days after a student applied for a job, we sent the student an email and asked them what happened. The email gave them four options:

1. “I never heard back.” If they selected this option, we encouraged them to find new jobs to apply to.
2. “I got an interview.” If they selected this option, we gave them tips for how to prepare for their interview.
3. “I got an offer.” If they selected this option, we gave them tips on how to evaluate and negotiate their offer.
4. “I got the job.” If they selected this option, we congratulated them.

Not everyone replied to our email. In fact, when we first launched it, only 5% of job applications (not applicants) netted a reply to the email. But over time, we grew that to 14%, and, by the time I left, we were at a 37% response rate. That’s not perfect, but it gave us some visibility into what was happening after an application. I know that if we had kept iterating on that email, the response rate would have continued to improve. We probably would have experimented with other ways of collecting the same data. We knew that, if we were relentless, we would find a way to track our desired outcome.

Here’s the key lesson. Just because the hire wasn’t happening on our platform didn’t mean it wasn’t valuable for us to measure it. We knew it was what would create value for our students, our employees, and ultimately our own business. So, we chipped away at it. We weren’t afraid to measure hard things—and you shouldn’t be, either.

Revisiting Different Types of Outcomes

In Chapter 3, we distinguished between business outcomes, product outcomes, and traction metrics as a way to help us set the scope for our product work. In the AfterCollege story, our product outcome was to improve search starts, and we succeeded at doing that. But our business outcome was to increase the number of students who found jobs on our platform. We had to continue to instrument our product to evaluate if driving our product outcome had the intended impact on our business outcome. This work took longer than expected. We didn’t want to wait to have the final answer before pushing value to our customers, so we continued to experiment in our production environment. Our discovery continued through to delivery.

This isn’t uncommon. However, in the AfterCollege story, it was easy for us to experiment in production. We were able to get a working prototype live in only a few days. Let’s return to our streaming-entertainment example to work through a more complex case. We can learn a lot about our subscribers’ interest in sports by running the assumption tests we defined in Chapter 10. However, to test if adding sports will drive our product outcome (to increase average minutes watched) and our business outcome (to increase subscriber retention), we’ll need to find small ways to experiment with real data—in other words, in our production environment.

We can’t test if watching sports on our platform will increase viewer minutes until we have sports on our platform. This might look like a Catch-22, but it’s not. We don’t need to test with the full solution to evaluate the impact on our outcomes. For example, we could partner with a local channel to stream one sporting event on one day and evaluate the impact on viewing minutes for the subscribers who watched that sporting event. We can look at whether their overall viewing minutes went up, or if they cut out content in other areas to make time for the sporting event. Integrating all local-channel content might require new business partnerships, contracts to be signed, and APIs to be developed. But starting with one event might allow you to circumvent a good chunk of that work, allowing both parties to test their assumptions before they commit to a longer-term agreement.

Just like in the AfterCollege story, it might take even more time to evaluate if sports content will drive the business outcome (increased subscriber retention). Streaming one sporting event likely won’t have a noticeable impact on subscriber numbers. However, if it impacts viewer minutes, we can keep investing, working on the belief that increasing viewing minutes will increase subscriber retention. The key in both examples is to remember to track the long-term connection between your product outcome and your business outcome. If, over time, an increase in viewing minutes doesn’t lead to an increase in subscriber retention, then the team will need to find a new product outcome that does drive the business outcome.

Avoid These Common Anti-Patterns

As you work to instrument your product and understand the impact of your product changes on your desired outcomes, avoid these common anti-patterns.

Getting stuck trying to measure everything. By far the most common mistake teams make when instrumenting their product is that they turn it into a massive waterfall project, in which they think they can define all of their needs upfront. Instead, start small. Instrument what you need to evaluate this week’s assumption tests. From there, work toward measuring the impact of your product changes on your product outcome. And with time, work to strengthen the connection between your product outcome and your business outcome.

Hyperfocusing on your assumption tests and forgetting to walk the lines of your opportunity solution tree. It’s exhilarating when our solutions start to work. It feels good when customers engage with what we build. But sadly, satisfying a customer need is not our only job. We need to remember that our goal is to satisfy customer needs while creating value for our business. We are constrained by driving our desired outcome. This is what allows us to create viable products, and viable products allow us to continue to serve our customers. So, when you find a compelling solution, remember to walk the lines of your opportunity solution tree. Desirability isn’t enough. Viability is the key to long-term success.

Forgetting to test the connection between your product outcome and your business outcome. Unfortunately, it’s not enough to drive product outcomes. The connection between our product outcome and our business outcome is a theory that needs to be tested. As you build a history of driving a product outcome, you need to remember to evaluate if driving the product outcome is, in turn, driving the business outcome. It’s what keeps our businesses thriving, allowing us to continue to serve our customers.