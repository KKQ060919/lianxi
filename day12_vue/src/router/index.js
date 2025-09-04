import {createMemoryHistory, createRouter} from 'vue-router'

import HelloWorld from '../components/HelloWorld.vue'
import 商品页面 from '../components/商品页面.vue'
import 热门商品 from '../components/热门商品.vue'
import RAG问答 from '../components/RAG问答.vue'
import Agents问答 from '../components/Agents问答.vue'

const routes = [
    { path: '/', component: HelloWorld, name: 'Home' },
    { path: '/products', component: 商品页面, name: 'Products' },
    { path: '/hot-products', component: 热门商品, name: 'HotProducts' },
    { path: '/rag-chat', component: RAG问答, name: 'RAGChat' },
    { path: '/agents-chat', component: Agents问答, name: 'AgentsChat' },
]

const router = createRouter({
    history: createMemoryHistory(),
    routes,
})

export default router