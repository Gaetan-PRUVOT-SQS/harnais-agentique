import { Annotation, END, MemorySaver, START, StateGraph } from "@langchain/langgraph";

const schema = Annotation.Root({
  n: Annotation({
    reducer: (left, right) => left + right,
    default: () => 0,
  }),
});

const graph = new StateGraph(schema)
  .addNode("plus", () => ({ n: 1 }))
  .addEdge(START, "plus")
  .addEdge("plus", END)
  .compile({ checkpointer: new MemorySaver() });

const out = await graph.invoke({}, { configurable: { thread_id: "preuve" } });
if (out.n !== 1) {
  process.exit(3);
}
process.stdout.write("somme 1\n");
